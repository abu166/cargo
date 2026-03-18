package data

// RegisterRequest запрос регистрации
type RegisterRequest struct {
	Email     string `json:"email"`
	Password  string `json:"password"`
	FirstName string `json:"first_name"`
	LastName  string `json:"last_name"`
}

// LoginRequest запрос входа
type LoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

// AuthResponse ответ аутентификации
type AuthResponse struct {
	Token     string `json:"token"`
	ExpiresIn int    `json:"expires_in"`
	UserID    string `json:"user_id"`
	Email     string `json:"email"`
}

// MeResponse ответ профиля
type MeResponse struct {
	ID        string `json:"id"`
	Email     string `json:"email"`
	FirstName string `json:"first_name"`
	LastName  string `json:"last_name"`
	Role      string `json:"role"`
	Station   string `json:"station"`
}

// CreateEmployeeRequest запрос создания сотрудника
type CreateEmployeeRequest struct {
	Email     string `json:"email"`
	FirstName string `json:"first_name"`
	LastName  string `json:"last_name"`
	Phone     string `json:"phone"`
	Role      string `json:"role"`
	Station   string `json:"station"`
}

// ListEmployeesResponse ответ списка сотрудников
type ListEmployeesResponse struct {
	Employees []EmployeeDTO `json:"employees"`
	Total     int           `json:"total"`
}

// EmployeeDTO DTO сотрудника
type EmployeeDTO struct {
	ID        string `json:"id"`
	Email     string `json:"email"`
	FirstName string `json:"first_name"`
	LastName  string `json:"last_name"`
	Phone     string `json:"phone"`
	Role      string `json:"role"`
	Station   string `json:"station"`
	IsActive  bool   `json:"is_active"`
}

// CreateCorporateClientRequest запрос создания корпоративного клиента
type CreateCorporateClientRequest struct {
	Name    string `json:"name"`
	Phone   string `json:"phone"`
	Email   string `json:"email"`
	Address string `json:"address"`
}

// CorporateClientDTO DTO корпоративного клиента
type CorporateClientDTO struct {
	ID      string  `json:"id"`
	Name    string  `json:"name"`
	Phone   string  `json:"phone"`
	Email   string  `json:"email"`
	Address string  `json:"address"`
	Balance float64 `json:"balance"`
}

// TopUpRequest запрос пополнения баланса
type TopUpRequest struct {
	ClientID string  `json:"client_id"`
	Amount   float64 `json:"amount"`
}
