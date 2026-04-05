package service

import (
	"context"
	"encoding/json"
	"fmt"
	"strconv"
	"strings"
	"time"

	"cargo/backend/internal/model"

	"github.com/google/uuid"
)

type DeliveryProviderAdapter interface {
	Quote(ctx context.Context, req DeliveryQuoteInput) (model.ExternalDeliveryQuote, error)
	CreateOrder(ctx context.Context, req DeliveryCreateOrderInput) (DeliveryCreateOrderResult, error)
	ParseWebhook(payload []byte) ([]DeliveryWebhookEvent, error)
}

type DeliveryQuoteInput struct {
	Shipment       model.Shipment
	DeliveryMode   model.DeliveryMode
	PickupDetails  *model.DeliveryPointDetails
	DropoffDetails *model.DeliveryPointDetails
}

type DeliveryCreateOrderInput struct {
	Shipment       model.Shipment
	Order          model.ExternalDeliveryOrder
	PickupDetails  *model.DeliveryPointDetails
	DropoffDetails *model.DeliveryPointDetails
}

type DeliveryCreateOrderResult struct {
	ExternalOrderID string
	Status          model.ExternalDeliveryStatus
	TrackingURL     *string
	RawResponse     *string
}

type DeliveryWebhookEvent struct {
	ExternalOrderID string                       `json:"external_order_id"`
	Status          model.ExternalDeliveryStatus `json:"status"`
	FinalPrice      *float64                     `json:"final_price,omitempty"`
	TrackingURL     *string                      `json:"tracking_url,omitempty"`
	Error           *string                      `json:"error,omitempty"`
}

type stubDeliveryAdapter struct {
	provider model.ExternalDeliveryProvider
}

func NewStubDeliveryAdapter(provider model.ExternalDeliveryProvider) DeliveryProviderAdapter {
	return &stubDeliveryAdapter{provider: provider}
}

func (s *stubDeliveryAdapter) Quote(_ context.Context, req DeliveryQuoteInput) (model.ExternalDeliveryQuote, error) {
	weight := parseWeight(req.Shipment.Weight)
	base := 1800.0 + (weight * 90)
	switch s.provider {
	case model.ProviderYandex:
		base *= 1.10
	case model.ProviderGlovo:
		base *= 1.05
	case model.ProviderInDrive:
		base *= 0.98
	}

	serviceLevel := "standard"
	eta := 5400
	if req.DeliveryMode == model.DeliveryModeHybrid {
		serviceLevel = "hybrid"
		eta = 7200
	}
	payload := fmt.Sprintf("{\"provider\":\"%s\",\"stub\":true}", s.provider)
	return model.ExternalDeliveryQuote{
		Provider:     s.provider,
		Price:        roundMoney(base),
		Currency:     "KZT",
		ETASeconds:   eta,
		ServiceLevel: serviceLevel,
		QuotationID:  uuid.NewString(),
		RawPayload:   &payload,
		CalculatedAt: time.Now().UTC(),
	}, nil
}

func (s *stubDeliveryAdapter) CreateOrder(_ context.Context, req DeliveryCreateOrderInput) (DeliveryCreateOrderResult, error) {
	externalID := strings.ToLower(string(s.provider)) + "-" + uuid.NewString()
	trackingURL := "https://tracking.example.local/" + externalID
	payload := fmt.Sprintf("{\"provider\":\"%s\",\"external_order_id\":\"%s\",\"stub\":true}", s.provider, externalID)
	status := model.ExternalDeliveryStatusCreated
	if req.Order.Status != "" {
		status = req.Order.Status
	}
	return DeliveryCreateOrderResult{
		ExternalOrderID: externalID,
		Status:          status,
		TrackingURL:     &trackingURL,
		RawResponse:     &payload,
	}, nil
}

func (s *stubDeliveryAdapter) ParseWebhook(payload []byte) ([]DeliveryWebhookEvent, error) {
	var body struct {
		Events []DeliveryWebhookEvent `json:"events"`
	}
	if err := json.Unmarshal(payload, &body); err != nil {
		return nil, fmt.Errorf("parse webhook: %w", err)
	}
	if len(body.Events) == 0 {
		return nil, fmt.Errorf("parse webhook: events are required")
	}
	return body.Events, nil
}

func parseWeight(weight string) float64 {
	trimmed := strings.TrimSpace(weight)
	if trimmed == "" {
		return 1
	}
	value, err := strconv.ParseFloat(trimmed, 64)
	if err != nil || value <= 0 {
		return 1
	}
	return value
}

func roundMoney(value float64) float64 {
	return float64(int(value*100+0.5)) / 100
}
