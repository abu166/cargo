package services

import (
	"errors"
	"strings"

	"cargo/backend/microservices/auth-service/core/domain/models"
)

var (
	ErrUnauthorized       = errors.New("unauthorized")
	ErrForbidden          = errors.New("forbidden")
	ErrInvalidCredentials = errors.New("invalid credentials")
	ErrDuplicateEmail     = errors.New("email already exists")
	ErrNotFound           = errors.New("not found")
	ErrInvalidTransition  = errors.New("invalid status transition")
	ErrInvalidState       = errors.New("invalid state")
)

type AuthService struct {
	repo      Repository
	jwtSecret string
}

type AdminService struct{ repo Repository }
type ClientService struct{ repo Repository }

type AuthenticatedUser struct {
	ID      string
	Email   string
	Role    models.Role
	Name    string
	Station string
}

type Repository interface {
	CreateUser(ctx interface{}, user models.User) (models.User, error)
	UpdateUser(ctx interface{}, user models.User) (models.User, error)
	GetUserByEmail(ctx interface{}, email string) (models.User, error)
	GetUserByID(ctx interface{}, id string) (models.User, error)
	ListUsers(ctx interface{}) ([]models.User, error)
	ListEmployees(ctx interface{}) ([]models.User, error)
	CreateEmployee(ctx interface{}, user models.User) (models.User, error)
	DeleteEmployee(ctx interface{}, id string) error
	ListCorporateClients(ctx interface{}) ([]models.User, error)
	TopUpDeposit(ctx interface{}, userID string, amount float64) (float64, error)
}

func normalizeEmail(email string) string {
	return strings.ToLower(strings.TrimSpace(email))
}
