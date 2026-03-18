package data

// AuditLogDTO DTO лога аудита
type AuditLogDTO struct {
	ID         int64  `json:"id"`
	EntityType string `json:"entity_type"`
	Action     string `json:"action"`
	UserId     string `json:"user_id"`
	Changes    string `json:"changes"`
	CreatedAt  string `json:"created_at"`
}

// ListAuditLogsResponse ответ списка логов аудита
type ListAuditLogsResponse struct {
	Logs  []AuditLogDTO `json:"logs"`
	Total int64         `json:"total"`
}
