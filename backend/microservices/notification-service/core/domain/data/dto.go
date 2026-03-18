package data

// NotificationDTO DTO уведомления
type NotificationDTO struct {
	ID        int64  `json:"id"`
	Message   string `json:"message"`
	IsRead    bool   `json:"is_read"`
	CreatedAt string `json:"created_at"`
}

// ListNotificationsResponse ответ списка уведомлений
type ListNotificationsResponse struct {
	Notifications []NotificationDTO `json:"notifications"`
	Total         int               `json:"total"`
	Unread        int               `json:"unread"`
}

// MarkReadRequest запрос отметить прочитанным
type MarkReadRequest struct {
	NotificationID int64 `json:"notification_id"`
}
