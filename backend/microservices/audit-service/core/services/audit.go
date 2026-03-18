package services

import (
	"context"

	"cargo/backend/microservices/audit-service/core/domain/models"
)

func (s *AuditService) List(ctx context.Context) ([]models.AuditLog, error) {
	return s.repo.ListAuditLogs(ctx)
}
