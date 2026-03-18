package services

import (
	"context"
	"errors"

	"cargo/backend/internal/model"
)

type ShipmentService struct{ repo Repository }

type AuthenticatedUser struct {
	ID      string
	Email   string
	Role    model.Role
	Name    string
	Station string
}

type Repository interface {
	CreateShipment(ctx context.Context, shipment model.Shipment) (model.Shipment, error)
	GetShipmentByID(ctx context.Context, id string) (model.Shipment, error)
	GetShipmentByTrackingCode(ctx context.Context, code string) (model.Shipment, error)
	ListShipments(ctx context.Context, filter model.ShipmentFilter) ([]model.Shipment, error)
	ListShipmentsByOriginStation(ctx context.Context, station string) ([]model.Shipment, error)
	UpdateShipment(ctx context.Context, shipment model.Shipment) (model.Shipment, error)
	AddShipmentHistory(ctx context.Context, history model.ShipmentHistory) error
	ListShipmentHistory(ctx context.Context, shipmentID string) ([]model.ShipmentHistory, error)
	CreateScanEvent(ctx context.Context, event model.ScanEvent) (model.ScanEvent, error)
	ListScanEvents(ctx context.Context, shipmentID string) ([]model.ScanEvent, error)
	CreateTransitEvent(ctx context.Context, event model.TransitEvent) (model.TransitEvent, error)
	ListTransitEvents(ctx context.Context, shipmentID string) ([]model.TransitEvent, error)
	CreateArrivalEvent(ctx context.Context, event model.ArrivalEvent) (model.ArrivalEvent, error)
	ListArrivalEvents(ctx context.Context, shipmentID string) ([]model.ArrivalEvent, error)
	CreateNotification(ctx context.Context, notification model.Notification) (model.Notification, error)
	AddAuditLog(ctx context.Context, log model.AuditLog) error
}

var (
	ErrUnauthorized       = errors.New("unauthorized")
	ErrForbidden          = errors.New("forbidden")
	ErrInvalidCredentials = errors.New("invalid credentials")
	ErrDuplicateEmail     = errors.New("email already exists")
	ErrNotFound           = errors.New("not found")
	ErrInvalidTransition  = errors.New("invalid status transition")
	ErrInvalidState       = errors.New("invalid state")
)

func ptr[T any](x T) *T {
	return &x
}

func legacyStatusForLifecycle(lifecycle model.ShipmentLifecycle) string {
	switch lifecycle {
	case model.ShipmentDraft:
		return "Черновик"
	case model.ShipmentCreated:
		return "Создан"
	case model.ShipmentPaymentPending:
		return "Ожидание оплаты"
	case model.ShipmentPaid:
		return "Оплачен"
	case model.ShipmentReadyForLoading:
		return "Готов к погрузке"
	case model.ShipmentLoaded:
		return "Погружен"
	case model.ShipmentInTransit:
		return "В пути"
	case model.ShipmentArrived:
		return "Прибыл"
	case model.ShipmentReadyForIssue:
		return "Готов к выдаче"
	case model.ShipmentIssued:
		return "Выдан"
	case model.ShipmentClosed:
		return "Закрыт"
	case model.ShipmentCancelled:
		return "Отменен"
	case model.ShipmentOnHold:
		return "На удержании"
	case model.ShipmentDamaged:
		return "Поврежден"
	default:
		return "Неизвестно"
	}
}

func calculateRoute(from, to string) []string {
	stationsOrder := []string{"Шымкент", "Алматы-1", "Қарағанды", "Астана Нұрлы Жол", "Ақтөбе"}
	fromIndex := indexOf(stationsOrder, from)
	toIndex := indexOf(stationsOrder, to)
	if fromIndex == -1 || toIndex == -1 {
		return []string{from, to}
	}
	if fromIndex < toIndex {
		return append([]string{}, stationsOrder[fromIndex:toIndex+1]...)
	}
	result := append([]string{}, stationsOrder[toIndex:fromIndex+1]...)
	for i, j := 0, len(result)-1; i < j; i, j = i+1, j-1 {
		result[i], result[j] = result[j], result[i]
	}
	return result
}

func indexOf(items []string, target string) int {
	for i, item := range items {
		if item == target {
			return i
		}
	}
	return -1
}
