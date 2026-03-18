package services

import (
	"context"

	"cargo/backend/microservices/audit-service/core/domain/models"
)

type AuditService struct{ repo Repository }

type Repository interface {
	ListAuditLogs(ctx context.Context) ([]models.AuditLog, error)
}
