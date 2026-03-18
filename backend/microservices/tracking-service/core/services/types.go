package services

import (
	"context"
	"errors"

	"cargo/backend/internal/model"
)

type TrackingService struct {
	repo Repository
}

type Repository interface {
	GetShipmentByID(ctx context.Context, id string) (model.Shipment, error)
	GetShipmentByTrackingCode(ctx context.Context, code string) (model.Shipment, error)
	UpdateShipment(ctx context.Context, shipment model.Shipment) (model.Shipment, error)
	CreateQRCode(ctx context.Context, code model.QRCode) (model.QRCode, error)
	CreateScanEvent(ctx context.Context, event model.ScanEvent) (model.ScanEvent, error)
	ListScanEvents(ctx context.Context, shipmentID string) ([]model.ScanEvent, error)
	ListShipmentHistory(ctx context.Context, shipmentID string) ([]model.ShipmentHistory, error)
	AddAuditLog(ctx context.Context, log model.AuditLog) error
}

var (
	ErrInvalidTransition = errors.New("invalid status transition")
)

func ptr[T any](x T) *T {
	return &x
}
