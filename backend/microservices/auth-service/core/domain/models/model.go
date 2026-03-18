package models

import "time"

// User модель пользователя
type User struct {
	ID           string
	Email        string
	PasswordHash string
	FirstName    string
	LastName     string
	Phone        string
	Role         Role
	IsActive     bool
	Station      string
	CreatedAt    time.Time
	UpdatedAt    time.Time
}

// Role роль пользователя
type Role string

const (
	RoleAdmin    Role = "admin"
	RoleOperator Role = "operator"
	RoleClient   Role = "client"
	RoleEmployee Role = "employee"
	RoleManager  Role = "manager"
)

// CorporateClient корпоративный клиент
type CorporateClient struct {
	ID        string
	Name      string
	Phone     string
	Email     string
	Address   string
	Users     []User
	Balance   float64
	CreatedAt time.Time
	UpdatedAt time.Time
}

// RoleRecord запись роли
type RoleRecord struct {
	ID    int
	Name  string
	Title string
}

// JWTClaims JWT claims
type JWTClaims struct {
	UserID string
	Email  string
	Role   Role
	Name   string
}
