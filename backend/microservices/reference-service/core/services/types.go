package services

import (
	"context"

	"cargo/backend/internal/model"
)

type ReferenceService struct{ repo Repository }

type Repository interface {
	ListRoles(ctx context.Context) ([]model.RoleRecord, error)
	ListStations(ctx context.Context) ([]model.Station, error)
	CreateStation(ctx context.Context, station model.Station) (model.Station, error)
	UpdateStation(ctx context.Context, station model.Station) (model.Station, error)
}
