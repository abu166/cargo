package data

// CreateShipmentRequest запрос создания отправления
type CreateShipmentRequest struct {
	SenderID           string  `json:"sender_id"`
	ReceiverID         string  `json:"receiver_id"`
	OriginStation      string  `json:"origin_station"`
	DestinationStation string  `json:"destination_station"`
	Description        string  `json:"description"`
	Weight             float64 `json:"weight"`
	Value              float64 `json:"value"`
	TariffRate         float64 `json:"tariff_rate"`
}

// ShipmentDTO DTO отправления
type ShipmentDTO struct {
	ID                 string   `json:"id"`
	Number             string   `json:"number"`
	TrackingCode       string   `json:"tracking_code"`
	Status             string   `json:"status"`
	Description        string   `json:"description"`
	Weight             float64  `json:"weight"`
	Value              float64  `json:"value"`
	TariffRate         float64  `json:"tariff_rate"`
	TotalPrice         float64  `json:"total_price"`
	OriginStation      string   `json:"origin_station"`
	DestinationStation string   `json:"destination_station"`
	CurrentStation     string   `json:"current_station"`
	Route              []string `json:"route"`
	CreatedAt          string   `json:"created_at"`
	UpdatedAt          string   `json:"updated_at"`
}

// EditShipmentRequest запрос редактирования отправления
type EditShipmentRequest struct {
	Description        string  `json:"description"`
	Weight             float64 `json:"weight"`
	Value              float64 `json:"value"`
	TariffRate         float64 `json:"tariff_rate"`
	DestinationStation string  `json:"destination_station"`
	OriginStation      string  `json:"origin_station"`
}

// CalculateTariffRequest запрос расчета тарифа
type CalculateTariffRequest struct {
	Weight   float64 `json:"weight"`
	Distance int     `json:"distance"`
	Value    float64 `json:"value"`
}

// ListShipmentsResponse ответ списка отправлений
type ListShipmentsResponse struct {
	Shipments []ShipmentDTO `json:"shipments"`
	Total     int           `json:"total"`
}

// ShipmentHistoryDTO DTO истории отправления
type ShipmentHistoryDTO struct {
	ID        int64  `json:"id"`
	Status    string `json:"status"`
	CreatedAt string `json:"created_at"`
}

// TransitEventDTO DTO события в пути
type TransitEventDTO struct {
	ID        int64  `json:"id"`
	Station   string `json:"station"`
	CreatedAt string `json:"created_at"`
}

// ArrivalEventDTO DTO события прибытия
type ArrivalEventDTO struct {
	ID        int64  `json:"id"`
	Station   string `json:"station"`
	CreatedAt string `json:"created_at"`
}

// ShipmentActionContext контекст действия над отправлением
type ShipmentActionContext struct {
	ShipmentID string
	UserId     string
	ActionType string
	Metadata   map[string]string
}
