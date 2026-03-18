package models

import "time"

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

// TransitEvent событие в пути
type TransitEvent struct {
	ID         int64
	ShipmentID string
	Station    string
	UserId     string
	CreatedAt  time.Time
}

// ArrivalEvent событие прибытия
type ArrivalEvent struct {
	ID         int64
	ShipmentID string
	Station    string
	UserId     string
	CreatedAt  time.Time
}

// ScanEvent событие сканирования
type ScanEvent struct {
	ID         int64
	ShipmentID string
	Station    string
	UserId     string
	CreatedAt  time.Time
}

// QRCode QR код
type QRCode struct {
	ID         int64
	ShipmentID string
	Code       string
	CreatedAt  time.Time
}

// ShipmentFilter фильтр для поиска отправлений
type ShipmentFilter struct {
	Status             string
	OriginStation      string
	DestinationStation string
	SenderID           string
	ReceiverID         string
	Limit              int
	Offset             int
}

// Notification уведомление
type Notification struct {
	ID        int64
	UserId    string
	Message   string
	IsRead    bool
	CreatedAt time.Time
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

// Station станция
type Station struct {
	ID        string
	Name      string
	City      string
	Code      string
	CreatedAt time.Time
	UpdatedAt time.Time
}
