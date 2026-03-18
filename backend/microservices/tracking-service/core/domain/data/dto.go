package data

// GenerateQRCodeRequest запрос генерации QR кода
type GenerateQRCodeRequest struct {
	ShipmentID string `json:"shipment_id"`
	UserId     string `json:"user_id"`
}

// QRCodeDTO DTO QR кода
type QRCodeDTO struct {
	ID         int64  `json:"id"`
	ShipmentID string `json:"shipment_id"`
	Code       string `json:"code"`
	CreatedAt  string `json:"created_at"`
}

// ScanEventRequest запрос события сканирования
type ScanEventRequest struct {
	ShipmentID string `json:"shipment_id"`
	Station    string `json:"station"`
	UserId     string `json:"user_id"`
}

// ScanEventDTO DTO события сканирования
type ScanEventDTO struct {
	ID         int64  `json:"id"`
	ShipmentID string `json:"shipment_id"`
	Station    string `json:"station"`
	CreatedAt  string `json:"created_at"`
}

// TrackingDTO DTO отслеживания
type TrackingDTO struct {
	ShipmentID   string               `json:"shipment_id"`
	TrackingCode string               `json:"tracking_code"`
	Status       string               `json:"status"`
	History      []ShipmentHistoryDTO `json:"history"`
	ScanEvents   []ScanEventDTO       `json:"scan_events"`
	CreatedAt    string               `json:"created_at"`
	UpdatedAt    string               `json:"updated_at"`
}

// ShipmentHistoryDTO DTO истории отправления
type ShipmentHistoryDTO struct {
	ID        int64  `json:"id"`
	Status    string `json:"status"`
	CreatedAt string `json:"created_at"`
}

// ListScanEventsResponse ответ списка событий сканирования
type ListScanEventsResponse struct {
	Events []ScanEventDTO `json:"events"`
	Total  int            `json:"total"`
}

// TrackingHistoryResponse ответ истории отслеживания
type TrackingHistoryResponse struct {
	ShipmentID string               `json:"shipment_id"`
	Status     string               `json:"status"`
	History    []ShipmentHistoryDTO `json:"history"`
}
