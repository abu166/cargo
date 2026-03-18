package services

import (
	"context"

	"cargo/backend/internal/model"
)

type NotificationService struct{ repo Repository }

type Repository interface {
	ListNotifications(ctx context.Context, userID string) ([]model.Notification, error)
	MarkNotificationRead(ctx context.Context, id int64) error
}
