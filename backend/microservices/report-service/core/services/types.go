package services

import (
	"context"

	"cargo/backend/internal/model"
)

type ReportService struct{ repo Repository }

type Repository interface {
	GetDashboardReport(ctx context.Context) (model.DashboardReport, error)
	GetFinanceReport(ctx context.Context) (model.FinanceReport, error)
	GetStatusSummary(ctx context.Context) ([]model.StatusSummaryItem, error)
}
