package data

// DashboardDTO DTO панели управления
type DashboardDTO struct {
	TotalShipments     int64   `json:"total_shipments"`
	ActiveShipments    int64   `json:"active_shipments"`
	CompletedShipments int64   `json:"completed_shipments"`
	TotalRevenue       float64 `json:"total_revenue"`
	PendingPayments    float64 `json:"pending_payments"`
	LastUpdated        string  `json:"last_updated"`
}

// FinanceDTO DTO финансовых данных
type FinanceDTO struct {
	TotalRevenue      float64 `json:"total_revenue"`
	TotalPayments     float64 `json:"total_payments"`
	PendingPayments   float64 `json:"pending_payments"`
	RefundedAmount    float64 `json:"refunded_amount"`
	AverageOrderValue float64 `json:"average_order_value"`
	Period            string  `json:"period"`
}

// StatusSummaryDTO DTO сводки статуса
type StatusSummaryDTO struct {
	Status     string  `json:"status"`
	Count      int64   `json:"count"`
	Percentage float64 `json:"percentage"`
}

// StatusSummaryResponse ответ сводки статуса
type StatusSummaryResponse struct {
	Items     []StatusSummaryDTO `json:"items"`
	Total     int64              `json:"total"`
	Timestamp string             `json:"timestamp"`
}
