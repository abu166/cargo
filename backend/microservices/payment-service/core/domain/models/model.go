package models

import "time"

// PaymentStatus статус платежа
type PaymentStatus string

const (
	PaymentPending   PaymentStatus = "PENDING"
	PaymentConfirmed PaymentStatus = "CONFIRMED"
	PaymentFailed    PaymentStatus = "FAILED"
	PaymentRefunded  PaymentStatus = "REFUNDED"
)

// Payment платеж
type Payment struct {
	ID         string
	ShipmentID string
	Amount     float64
	Status     PaymentStatus
	UserId     string
	CreatedAt  time.Time
	UpdatedAt  time.Time
}

// ShipmentLifecycle статусы жизненного цикла отправления
type ShipmentLifecycle string

const (
	ShipmentDraft           ShipmentLifecycle = "DRAFT"
	ShipmentCreated         ShipmentLifecycle = "CREATED"
	ShipmentPaymentPending  ShipmentLifecycle = "PAYMENT_PENDING"
	ShipmentPaid            ShipmentLifecycle = "PAID"
	ShipmentReadyForLoading ShipmentLifecycle = "READY_FOR_LOADING"
	ShipmentLoaded          ShipmentLifecycle = "LOADED"
	ShipmentInTransit       ShipmentLifecycle = "IN_TRANSIT"
	ShipmentArrived         ShipmentLifecycle = "ARRIVED"
	ShipmentReadyForIssue   ShipmentLifecycle = "READY_FOR_ISSUE"
	ShipmentIssued          ShipmentLifecycle = "ISSUED"
	ShipmentClosed          ShipmentLifecycle = "CLOSED"
	ShipmentCancelled       ShipmentLifecycle = "CANCELLED"
	ShipmentOnHold          ShipmentLifecycle = "ON_HOLD"
	ShipmentDamaged         ShipmentLifecycle = "DAMAGED"
)

// Shipment отправление
type Shipment struct {
	ID                 string
	Number             string
	TrackingCode       string
	SenderID           string
	ReceiverID         string
	OriginStation      string
	DestinationStation string
	Status             ShipmentLifecycle
	Description        string
	Weight             float64
	Value              float64
	TariffRate         float64
	TotalPrice         float64
	CurrentStation     string
	Route              []string
	CreatedAt          time.Time
	UpdatedAt          time.Time
	ClosedAt           *time.Time
}

// ShipmentHistory история отправления
type ShipmentHistory struct {
	ID         int64
	ShipmentID string
	Status     string
	UserId     string
	CreatedAt  time.Time
}

// AuditLog лог аудита
type AuditLog struct {
	ID         int64
	EntityType string
	Action     string
	UserId     string
	Changes    string
	CreatedAt  time.Time
}
