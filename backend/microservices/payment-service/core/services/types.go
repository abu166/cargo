package services

import (
	"context"
	"errors"

	"cargo/backend/internal/model"
)

type PaymentService struct {
	repo Repository
}

type Repository interface {
	CreatePayment(ctx context.Context, payment model.Payment) (model.Payment, error)
	GetPayment(ctx context.Context, id string) (model.Payment, error)
	UpdatePayment(ctx context.Context, payment model.Payment) (model.Payment, error)
	GetShipmentByID(ctx context.Context, id string) (model.Shipment, error)
	UpdateShipment(ctx context.Context, shipment model.Shipment) (model.Shipment, error)
	AddShipmentHistory(ctx context.Context, history model.ShipmentHistory) error
	AddAuditLog(ctx context.Context, log model.AuditLog) error
}

var (
	ErrInvalidTransition = errors.New("invalid status transition")
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
