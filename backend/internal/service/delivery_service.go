package service

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"cargo/backend/internal/model"

	"github.com/google/uuid"
)

type DeliveryService struct {
	repo      Repository
	providers map[model.ExternalDeliveryProvider]DeliveryProviderAdapter
}

type QuoteDeliveryRequest struct {
	DeliveryMode   model.DeliveryMode               `json:"delivery_mode"`
	PickupDetails  *model.DeliveryPointDetails      `json:"pickup_details,omitempty"`
	DropoffDetails *model.DeliveryPointDetails      `json:"dropoff_details,omitempty"`
	Providers      []model.ExternalDeliveryProvider `json:"providers,omitempty"`
}

type CreateDeliveryOrderRequest struct {
	Provider       model.ExternalDeliveryProvider `json:"provider"`
	DeliveryMode   model.DeliveryMode             `json:"delivery_mode"`
	PickupDetails  *model.DeliveryPointDetails    `json:"pickup_details,omitempty"`
	DropoffDetails *model.DeliveryPointDetails    `json:"dropoff_details,omitempty"`
	QuotedPrice    float64                        `json:"quoted_price"`
	Currency       string                         `json:"currency"`
	IdempotencyKey string                         `json:"idempotency_key"`
}

func (s *DeliveryService) Quote(ctx context.Context, shipmentID string, req QuoteDeliveryRequest) (model.Shipment, []model.ExternalDeliveryQuote, error) {
	shipment, err := s.repo.GetShipmentByID(ctx, shipmentID)
	if err != nil {
		return model.Shipment{}, nil, err
	}
	if req.DeliveryMode == "" {
		req.DeliveryMode = model.DeliveryModeCourierPickup
	}
	if err := validateDeliveryInput(req.DeliveryMode, req.PickupDetails, req.DropoffDetails); err != nil {
		return model.Shipment{}, nil, err
	}
	providers := req.Providers
	if len(providers) == 0 {
		providers = []model.ExternalDeliveryProvider{model.ProviderYandex, model.ProviderGlovo, model.ProviderInDrive}
	}

	quotes := make([]model.ExternalDeliveryQuote, 0, len(providers))
	for _, provider := range providers {
		adapter, ok := s.providers[provider]
		if !ok {
			continue
		}
		quote, err := adapter.Quote(ctx, DeliveryQuoteInput{
			Shipment:       shipment,
			DeliveryMode:   req.DeliveryMode,
			PickupDetails:  req.PickupDetails,
			DropoffDetails: req.DropoffDetails,
		})
		if err != nil {
			return model.Shipment{}, nil, err
		}
		quotes = append(quotes, quote)
	}
	if len(quotes) == 0 {
		return model.Shipment{}, nil, fmt.Errorf("%w: no supported providers in request", ErrValidation)
	}
	return shipment, quotes, nil
}

func (s *DeliveryService) CreateOrder(ctx context.Context, shipmentID string, req CreateDeliveryOrderRequest, operatorID *string) (model.Shipment, model.ExternalDeliveryOrder, error) {
	shipment, err := s.repo.GetShipmentByID(ctx, shipmentID)
	if err != nil {
		return model.Shipment{}, model.ExternalDeliveryOrder{}, err
	}
	if req.Provider == "" {
		return model.Shipment{}, model.ExternalDeliveryOrder{}, fmt.Errorf("%w: provider is required", ErrValidation)
	}
	adapter, ok := s.providers[req.Provider]
	if !ok {
		return model.Shipment{}, model.ExternalDeliveryOrder{}, fmt.Errorf("%w: unsupported provider", ErrValidation)
	}
	if req.DeliveryMode == "" {
		req.DeliveryMode = model.DeliveryModeCourierPickup
	}
	if err := validateDeliveryInput(req.DeliveryMode, req.PickupDetails, req.DropoffDetails); err != nil {
		return model.Shipment{}, model.ExternalDeliveryOrder{}, err
	}
	if req.QuotedPrice <= 0 {
		return model.Shipment{}, model.ExternalDeliveryOrder{}, fmt.Errorf("%w: quoted_price must be > 0", ErrValidation)
	}
	if strings.TrimSpace(req.Currency) == "" {
		req.Currency = "KZT"
	}
	if req.IdempotencyKey == "" {
		req.IdempotencyKey = uuid.NewString()
	}

	requestRaw := rawJSONString(req)
	order := model.ExternalDeliveryOrder{
		ID:             uuid.NewString(),
		ShipmentID:     shipmentID,
		Provider:       req.Provider,
		Status:         model.ExternalDeliveryStatusQuoted,
		QuotedPrice:    req.QuotedPrice,
		Currency:       req.Currency,
		IdempotencyKey: req.IdempotencyKey,
		RequestPayload: requestRaw,
		CreatedAt:      time.Now().UTC(),
		UpdatedAt:      time.Now().UTC(),
	}
	result, err := adapter.CreateOrder(ctx, DeliveryCreateOrderInput{
		Shipment:       shipment,
		Order:          order,
		PickupDetails:  req.PickupDetails,
		DropoffDetails: req.DropoffDetails,
	})
	if err != nil {
		return model.Shipment{}, model.ExternalDeliveryOrder{}, err
	}
	order.ExternalOrderID = &result.ExternalOrderID
	order.Status = result.Status
	order.TrackingURL = result.TrackingURL
	order.ResponsePayload = result.RawResponse
	order.UpdatedAt = time.Now().UTC()
	storedOrder, err := s.repo.CreateExternalDeliveryOrder(ctx, order)
	if err != nil {
		return model.Shipment{}, model.ExternalDeliveryOrder{}, err
	}

	base := shipment.BaseTariff
	if base <= 0 {
		base = shipment.Cost
	}
	shipment.BaseTariff = base
	shipment.FirstMileTariff = req.QuotedPrice
	shipment.LastMileTariff = 0
	if req.DeliveryMode == model.DeliveryModeHybrid {
		shipment.LastMileTariff = req.QuotedPrice
	}
	shipment.TotalTariff = shipment.BaseTariff + shipment.FirstMileTariff + shipment.LastMileTariff
	shipment.Cost = shipment.TotalTariff
	shipment.DeliveryMode = req.DeliveryMode
	shipment.PickupDetails = req.PickupDetails
	shipment.DropoffDetails = req.DropoffDetails
	shipment.UpdatedAt = time.Now().UTC()
	shipment.LastUpdatedAt = shipment.UpdatedAt
	updatedShipment, err := s.repo.UpdateShipment(ctx, shipment)
	if err != nil {
		return model.Shipment{}, model.ExternalDeliveryOrder{}, err
	}

	_ = s.repo.AddShipmentHistory(ctx, model.ShipmentHistory{
		ShipmentID: updatedShipment.ID,
		Action:     "External delivery order created",
		OperatorID: operatorID,
		Details:    fmt.Sprintf("Provider %s, external order %s", req.Provider, result.ExternalOrderID),
		CreatedAt:  time.Now().UTC(),
	})
	return updatedShipment, storedOrder, nil
}

func (s *DeliveryService) HandleWebhook(ctx context.Context, provider model.ExternalDeliveryProvider, payload []byte) (int, error) {
	adapter, ok := s.providers[provider]
	if !ok {
		return 0, fmt.Errorf("%w: unsupported provider", ErrValidation)
	}
	events, err := adapter.ParseWebhook(payload)
	if err != nil {
		return 0, err
	}
	updatedCount := 0
	for _, event := range events {
		if event.ExternalOrderID == "" {
			continue
		}
		order, err := s.repo.GetExternalDeliveryOrderByExternalID(ctx, provider, event.ExternalOrderID)
		if err != nil {
			continue
		}
		order.Status = event.Status
		order.FinalPrice = event.FinalPrice
		order.TrackingURL = event.TrackingURL
		order.LastError = event.Error
		order.UpdatedAt = time.Now().UTC()
		if _, err := s.repo.UpdateExternalDeliveryOrder(ctx, order); err != nil {
			continue
		}
		updatedCount++
	}
	return updatedCount, nil
}

func validateDeliveryInput(mode model.DeliveryMode, pickup, dropoff *model.DeliveryPointDetails) error {
	switch mode {
	case model.DeliveryModeSelfDropOff:
		return nil
	case model.DeliveryModeCourierPickup:
		if pickup == nil {
			return fmt.Errorf("%w: pickup_details are required", ErrValidation)
		}
	case model.DeliveryModeHybrid:
		if pickup == nil {
			return fmt.Errorf("%w: pickup_details are required", ErrValidation)
		}
		if dropoff == nil {
			return fmt.Errorf("%w: dropoff_details are required", ErrValidation)
		}
	default:
		return fmt.Errorf("%w: unsupported delivery_mode", ErrValidation)
	}
	return nil
}

func rawJSONString(value any) *string {
	encoded, err := json.Marshal(value)
	if err != nil {
		return nil
	}
	result := string(encoded)
	return &result
}
