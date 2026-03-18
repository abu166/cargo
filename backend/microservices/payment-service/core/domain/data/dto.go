package data

// CreatePaymentRequest запрос создания платежа
type CreatePaymentRequest struct {
	ShipmentID string  `json:"shipment_id"`
	Amount     float64 `json:"amount"`
	UserId     string  `json:"user_id"`
}

// PaymentDTO DTO платежа
type PaymentDTO struct {
	ID         string  `json:"id"`
	ShipmentID string  `json:"shipment_id"`
	Amount     float64 `json:"amount"`
	Status     string  `json:"status"`
	CreatedAt  string  `json:"created_at"`
	UpdatedAt  string  `json:"updated_at"`
}

// ConfirmPaymentRequest запрос подтверждения платежа
type ConfirmPaymentRequest struct {
	PaymentID string `json:"payment_id"`
	UserId    string `json:"user_id"`
}

// PaymentResponse ответ платежа
type PaymentResponse struct {
	ID         string  `json:"id"`
	ShipmentID string  `json:"shipment_id"`
	Amount     float64 `json:"amount"`
	Status     string  `json:"status"`
	CreatedAt  string  `json:"created_at"`
	UpdatedAt  string  `json:"updated_at"`
}
