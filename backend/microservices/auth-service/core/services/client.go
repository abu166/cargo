package services

import (
	"context"
	"errors"
	"time"

	"cargo/backend/microservices/auth-service/core/domain/models"

	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
)

func (s *ClientService) ListCorporateClients(ctx context.Context) ([]models.User, error) {
	return s.repo.ListCorporateClients(ctx)
}

func (s *ClientService) TopUp(ctx context.Context, userID string, amount float64) (float64, error) {
	return s.repo.TopUpDeposit(ctx, userID, amount)
}

func (s *ClientService) CreateCorporateClient(ctx context.Context, name, email, password, company, contractNumber string, phone *string, deposit float64) (models.User, error) {
	email = normalizeEmail(email)
	_, err := s.repo.GetUserByEmail(ctx, email)
	if err == nil {
		return models.User{}, ErrDuplicateEmail
	}
	if !errors.Is(err, ErrNotFound) {
		return models.User{}, err
	}
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return models.User{}, err
	}
	user := models.User{
		ID:             uuid.NewString(),
		Name:           name,
		Email:          email,
		PasswordHash:   string(hash),
		Role:           models.RoleCorporate,
		Company:        &company,
		DepositBalance: deposit,
		ContractNumber: &contractNumber,
		Phone:          phone,
		IsActive:       true,
		CreatedAt:      time.Now().UTC(),
	}
	return s.repo.CreateUser(ctx, user)
}
