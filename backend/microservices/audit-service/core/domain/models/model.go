package models

import "time"

// AuditLog лог аудита
type AuditLog struct {
	ID         int64
	EntityType string
	Action     string
	UserId     string
	Changes    string
	CreatedAt  time.Time
}
