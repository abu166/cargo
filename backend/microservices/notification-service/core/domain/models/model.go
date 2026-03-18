package models

import "time"

// Notification уведомление
type Notification struct {
	ID        int64
	UserId    string
	Message   string
	IsRead    bool
	CreatedAt time.Time
}
