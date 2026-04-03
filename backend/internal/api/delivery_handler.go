package api

import (
	"io"
	"net/http"
	"strings"

	"cargo/backend/internal/model"
	"cargo/backend/internal/service"

	"github.com/go-chi/chi/v5"
)

func (s *Server) mountDeliveryRoutes(r chi.Router) {
	r.Post("/shipments/{id}/delivery/quote", s.handleDeliveryQuote)
	r.Post("/shipments/{id}/delivery/order", s.handleDeliveryCreateOrder)
	r.Post("/delivery/webhook/{provider}", s.handleDeliveryWebhook)
}

func (s *Server) handleDeliveryQuote(w http.ResponseWriter, r *http.Request) {
	user, ok := s.mustAuth(w, r)
	if !ok {
		return
	}
	if err := s.requireRole(user, model.RoleOperator, model.RoleManager, model.RoleAdmin); err != nil {
		handleServiceError(w, err)
		return
	}
	var req struct {
		DeliveryMode   model.DeliveryMode          `json:"delivery_mode"`
		PickupDetails  *model.DeliveryPointDetails `json:"pickup_details,omitempty"`
		DropoffDetails *model.DeliveryPointDetails `json:"dropoff_details,omitempty"`
		Providers      []string                    `json:"providers,omitempty"`
	}
	if !decodeJSON(w, r, &req) {
		return
	}
	providers := make([]model.ExternalDeliveryProvider, 0, len(req.Providers))
	for _, providerRaw := range req.Providers {
		provider, ok := parseProvider(providerRaw)
		if !ok {
			continue
		}
		providers = append(providers, provider)
	}
	shipment, quotes, err := s.services.Delivery.Quote(r.Context(), chi.URLParam(r, "id"), service.QuoteDeliveryRequest{
		DeliveryMode:   req.DeliveryMode,
		PickupDetails:  req.PickupDetails,
		DropoffDetails: req.DropoffDetails,
		Providers:      providers,
	})
	if err != nil {
		handleServiceError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"shipment": shipment, "quotes": quotes})
}

func (s *Server) handleDeliveryCreateOrder(w http.ResponseWriter, r *http.Request) {
	user, ok := s.mustAuth(w, r)
	if !ok {
		return
	}
	if err := s.requireRole(user, model.RoleOperator, model.RoleManager, model.RoleAdmin); err != nil {
		handleServiceError(w, err)
		return
	}
	var req struct {
		Provider       string                      `json:"provider"`
		DeliveryMode   model.DeliveryMode          `json:"delivery_mode"`
		PickupDetails  *model.DeliveryPointDetails `json:"pickup_details,omitempty"`
		DropoffDetails *model.DeliveryPointDetails `json:"dropoff_details,omitempty"`
		QuotedPrice    float64                     `json:"quoted_price"`
		Currency       string                      `json:"currency"`
		IdempotencyKey string                      `json:"idempotency_key"`
	}
	if !decodeJSON(w, r, &req) {
		return
	}
	provider, ok := parseProvider(req.Provider)
	if !ok {
		writeError(w, http.StatusBadRequest, "provider is invalid")
		return
	}
	shipment, order, err := s.services.Delivery.CreateOrder(r.Context(), chi.URLParam(r, "id"), service.CreateDeliveryOrderRequest{
		Provider:       provider,
		DeliveryMode:   req.DeliveryMode,
		PickupDetails:  req.PickupDetails,
		DropoffDetails: req.DropoffDetails,
		QuotedPrice:    req.QuotedPrice,
		Currency:       req.Currency,
		IdempotencyKey: req.IdempotencyKey,
	}, &user.ID)
	if err != nil {
		handleServiceError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"shipment": shipment, "external_delivery_order": order})
}

func (s *Server) handleDeliveryWebhook(w http.ResponseWriter, r *http.Request) {
	provider, ok := parseProvider(chi.URLParam(r, "provider"))
	if !ok {
		writeError(w, http.StatusBadRequest, "provider is invalid")
		return
	}
	payload, err := io.ReadAll(r.Body)
	if err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}
	count, err := s.services.Delivery.HandleWebhook(r.Context(), provider, payload)
	if err != nil {
		handleServiceError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"updated": count})
}

func parseProvider(raw string) (model.ExternalDeliveryProvider, bool) {
	switch strings.ToUpper(strings.TrimSpace(raw)) {
	case string(model.ProviderYandex):
		return model.ProviderYandex, true
	case string(model.ProviderGlovo):
		return model.ProviderGlovo, true
	case string(model.ProviderInDrive):
		return model.ProviderInDrive, true
	default:
		return "", false
	}
}
