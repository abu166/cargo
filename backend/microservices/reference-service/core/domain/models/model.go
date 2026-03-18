package models

import "time"

// Station станция
type Station struct {
	ID        string
	Name      string
	City      string
	Code      string
	CreatedAt time.Time
	UpdatedAt time.Time
}

// RoleRecord запись роли
type RoleRecord struct {
	ID    int
	Name  string
	Title string
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
