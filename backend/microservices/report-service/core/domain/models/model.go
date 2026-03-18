package models

// DashboardReport отчет панели
type DashboardReport struct {
	TotalShipments     int64
	ActiveShipments    int64
	CompletedShipments int64
	TotalRevenue       float64
	PendingPayments    float64
	LastUpdated        string
}

// FinanceReport финансовый отчет
type FinanceReport struct {
	TotalRevenue      float64
	TotalPayments     float64
	PendingPayments   float64
	RefundedAmount    float64
	AverageOrderValue float64
	Period            string
}

// StatusSummaryItem элемент сводки статуса
type StatusSummaryItem struct {
	Status     string
	Count      int64
	Percentage float64
}
