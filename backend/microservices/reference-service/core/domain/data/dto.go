package data

// CreateStationRequest запрос создания станции
type CreateStationRequest struct {
	Name string `json:"name"`
	City string `json:"city"`
	Code string `json:"code"`
}

// StationDTO DTO станции
type StationDTO struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	City      string `json:"city"`
	Code      string `json:"code"`
	CreatedAt string `json:"created_at"`
	UpdatedAt string `json:"updated_at"`
}

// UpdateStationRequest запрос обновления станции
type UpdateStationRequest struct {
	Name string `json:"name"`
	City string `json:"city"`
	Code string `json:"code"`
}

// RoleDTO DTO роли
type RoleDTO struct {
	ID    int    `json:"id"`
	Name  string `json:"name"`
	Title string `json:"title"`
}

// ListStationsResponse ответ списка станций
type ListStationsResponse struct {
	Stations []StationDTO `json:"stations"`
	Total    int          `json:"total"`
}

// ListRolesResponse ответ списка ролей
type ListRolesResponse struct {
	Roles []RoleDTO `json:"roles"`
	Total int       `json:"total"`
}
