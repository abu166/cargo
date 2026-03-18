# Hexagonal Architecture - Implementation Examples

This document provides concrete code examples for implementing hexagonal architecture in CargoGO.

## Example 1: ShipmentService with Ports

### The Port Definition (What the service needs)

```go
// internal/domain/ports/shipment_repository.go
package ports

import (
    "context"
    "cargo/backend/internal/model"
)

type ShipmentRepository interface {
    CreateShipment(ctx context.Context, shipment *model.Shipment) (*model.Shipment, error)
    GetShipmentByID(ctx context.Context, id string) (*model.Shipment, error)
    UpdateShipment(ctx context.Context, shipment *model.Shipment) (*model.Shipment, error)
    ListShipments(ctx context.Context, filter *model.ShipmentFilter) ([]model.Shipment, error)
    GetShipmentByTrackingCode(ctx context.Context, code string) (*model.Shipment, error)
    AddShipmentHistory(ctx context.Context, history *model.ShipmentHistory) error
}

type EventPublisher interface {
    PublishShipmentCreated(ctx context.Context, shipmentID string, shipment *model.Shipment) error
    PublishShipmentStatusChanged(ctx context.Context, shipmentID string, oldStatus, newStatus model.ShipmentLifecycle) error
}

type Logger interface {
    Info(msg string, fields ...interface{})
    Error(msg string, err error, fields ...interface{})
}
```

### The Service (Business Logic)

```go
// internal/domain/service/shipment_service.go
package service

import (
    "context"
    "errors"

    "cargo/backend/internal/domain/ports"
    "cargo/backend/internal/model"
)

type ShipmentService struct {
    repo           ports.ShipmentRepository
    eventPublisher ports.EventPublisher
    logger         ports.Logger
}

func NewShipmentService(
    repo ports.ShipmentRepository,
    eventPublisher ports.EventPublisher,
    logger ports.Logger,
) *ShipmentService {
    return &ShipmentService{
        repo:           repo,
        eventPublisher: eventPublisher,
        logger:         logger,
    }
}

// CreateShipment creates a new shipment
func (s *ShipmentService) CreateShipment(ctx context.Context, shipment *model.Shipment) (*model.Shipment, error) {
    // Validate shipment
    if err := s.validateShipment(shipment); err != nil {
        s.logger.Error("invalid shipment", err)
        return nil, err
    }

    // Generate shipment number
    shipment.ShipmentNumber = s.generateShipmentNumber()
    shipment.ShipmentStatus = model.ShipmentCreated
    shipment.PaymentStatus = model.PaymentUnpaid

    // Create in repository
    created, err := s.repo.CreateShipment(ctx, shipment)
    if err != nil {
        s.logger.Error("failed to create shipment", err)
        return nil, err
    }

    // Publish event
    if err := s.eventPublisher.PublishShipmentCreated(ctx, created.ID, created); err != nil {
        s.logger.Error("failed to publish shipment created event", err)
        // Don't fail the request, but log it
    }

    s.logger.Info("shipment created", "shipment_id", created.ID)
    return created, nil
}

// UpdateShipmentStatus changes the shipment status
func (s *ShipmentService) UpdateShipmentStatus(
    ctx context.Context,
    shipmentID string,
    newStatus model.ShipmentLifecycle,
    operatorID string,
) error {
    // Get current shipment
    shipment, err := s.repo.GetShipmentByID(ctx, shipmentID)
    if err != nil {
        return errors.New("shipment not found")
    }

    oldStatus := shipment.ShipmentStatus

    // Validate state transition
    if !isValidTransition(oldStatus, newStatus) {
        return errors.New("invalid status transition")
    }

    // Update status
    shipment.ShipmentStatus = newStatus
    shipment.LastUpdatedAt = time.Now()

    // Persist
    _, err = s.repo.UpdateShipment(ctx, shipment)
    if err != nil {
        s.logger.Error("failed to update shipment", err)
        return err
    }

    // Add to history
    history := &model.ShipmentHistory{
        ShipmentID:   shipmentID,
        Action:       "STATUS_CHANGED",
        OperatorID:   &operatorID,
        OldStatus:    (*string)(&oldStatus),
        NewStatus:    (*string)(&newStatus),
        Details:      "Status transitioned",
        CreatedAt:    time.Now(),
    }
    if err := s.repo.AddShipmentHistory(ctx, history); err != nil {
        s.logger.Error("failed to add shipment history", err)
    }

    // Publish event
    if err := s.eventPublisher.PublishShipmentStatusChanged(ctx, shipmentID, oldStatus, newStatus); err != nil {
        s.logger.Error("failed to publish status changed event", err)
    }

    return nil
}

func (s *ShipmentService) validateShipment(shipment *model.Shipment) error {
    if shipment.ClientID == "" {
        return errors.New("client_id is required")
    }
    if shipment.FromStation == "" {
        return errors.New("from_station is required")
    }
    if shipment.ToStation == "" {
        return errors.New("to_station is required")
    }
    return nil
}

func (s *ShipmentService) generateShipmentNumber() string {
    // Implementation
    return fmt.Sprintf("SHIP-%s-%d", time.Now().Format("20060102"), rand.Intn(10000))
}

func isValidTransition(from, to model.ShipmentLifecycle) bool {
    // Define valid transitions
    transitions := map[model.ShipmentLifecycle][]model.ShipmentLifecycle{
        model.ShipmentCreated: {model.ShipmentPaymentPending, model.ShipmentCancelled},
        model.ShipmentPaymentPending: {model.ShipmentPaid, model.ShipmentCancelled},
        model.ShipmentPaid: {model.ShipmentReadyForLoading, model.ShipmentCancelled},
        // ... more transitions
    }
    
    for _, valid := range transitions[from] {
        if valid == to {
            return true
        }
    }
    return false
}
```

## Example 2: API Handler with DTOs

### DTOs (Request/Response Models)

```go
// internal/api/dto/shipment_request.go
package dto

type CreateShipmentRequest struct {
    ClientID       string `json:"client_id" validate:"required"`
    FromStation    string `json:"from_station" validate:"required"`
    ToStation      string `json:"to_station" validate:"required"`
    Weight         string `json:"weight" validate:"required"`
    Dimensions     string `json:"dimensions" validate:"required"`
    Description    string `json:"description" validate:"required"`
    QuantityPlaces int    `json:"quantity_places" validate:"required,min=1"`
    ReceiverName   string `json:"receiver_name,omitempty"`
    ReceiverPhone  string `json:"receiver_phone,omitempty"`
}

type UpdateShipmentStatusRequest struct {
    Status string `json:"status" validate:"required"`
    Reason string `json:"reason,omitempty"`
}

// internal/api/dto/shipment_response.go
package dto

type ShipmentResponse struct {
    ID              string `json:"id"`
    ShipmentNumber  string `json:"shipment_number"`
    ClientID        string `json:"client_id"`
    FromStation     string `json:"from_station"`
    ToStation       string `json:"to_station"`
    CurrentStation  string `json:"current_station"`
    Status          string `json:"status"`
    ShipmentStatus  string `json:"shipment_status"`
    PaymentStatus   string `json:"payment_status"`
    Cost            float64 `json:"cost"`
    TrackingCode    string `json:"tracking_code,omitempty"`
    CreatedAt       string `json:"created_at"`
    LastUpdatedAt   string `json:"last_updated_at"`
}

type ErrorResponse struct {
    Code    string `json:"code"`
    Message string `json:"message"`
    Details map[string]string `json:"details,omitempty"`
}

// Mapper
func ShipmentToResponse(s *model.Shipment) *ShipmentResponse {
    return &ShipmentResponse{
        ID:             s.ID,
        ShipmentNumber: s.ShipmentNumber,
        ClientID:       s.ClientID,
        FromStation:    s.FromStation,
        ToStation:      s.ToStation,
        CurrentStation: s.CurrentStation,
        Status:         s.Status,
        ShipmentStatus: string(s.ShipmentStatus),
        PaymentStatus:  string(s.PaymentStatus),
        Cost:           s.Cost,
        TrackingCode:   valueOrEmpty(s.TrackingCode),
        CreatedAt:      s.CreatedAt.Format(time.RFC3339),
        LastUpdatedAt:  s.LastUpdatedAt.Format(time.RFC3339),
    }
}

func valueOrEmpty(v *string) string {
    if v == nil {
        return ""
    }
    return *v
}
```

### HTTP Handler (Incoming Adapter)

```go
// internal/api/handlers/shipment_handler.go
package handlers

import (
    "encoding/json"
    "errors"
    "net/http"

    "cargo/backend/internal/api/dto"
    "cargo/backend/internal/domain/service"
    "cargo/backend/internal/model"
)

type ShipmentHandler struct {
    shipmentService *service.ShipmentService
    logger          ports.Logger
}

func NewShipmentHandler(
    shipmentService *service.ShipmentService,
    logger ports.Logger,
) *ShipmentHandler {
    return &ShipmentHandler{
        shipmentService: shipmentService,
        logger:          logger,
    }
}

// CreateShipment handles POST /api/shipments
func (h *ShipmentHandler) CreateShipment(w http.ResponseWriter, r *http.Request) {
    var req dto.CreateShipmentRequest

    // Parse and validate request
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        h.respondError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body", err)
        return
    }

    // Validate
    if err := h.validate(req); err != nil {
        h.respondError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error(), nil)
        return
    }

    // Convert DTO to domain model
    shipment := &model.Shipment{
        ClientID:       req.ClientID,
        FromStation:    req.FromStation,
        ToStation:      req.ToStation,
        Weight:         req.Weight,
        Dimensions:     req.Dimensions,
        Description:    req.Description,
        QuantityPlaces: req.QuantityPlaces,
        ReceiverName:   &req.ReceiverName,
        ReceiverPhone:  &req.ReceiverPhone,
    }

    // Call service
    created, err := h.shipmentService.CreateShipment(r.Context(), shipment)
    if err != nil {
        h.logger.Error("failed to create shipment", err)
        h.respondError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Failed to create shipment", err)
        return
    }

    // Convert response
    response := dto.ShipmentToResponse(created)
    h.respondSuccess(w, http.StatusCreated, response)
}

// GetShipment handles GET /api/shipments/:id
func (h *ShipmentHandler) GetShipment(w http.ResponseWriter, r *http.Request) {
    shipmentID := chi.URLParam(r, "id")

    shipment, err := h.shipmentService.GetShipment(r.Context(), shipmentID)
    if err != nil {
        if errors.Is(err, service.ErrNotFound) {
            h.respondError(w, http.StatusNotFound, "NOT_FOUND", "Shipment not found", nil)
        } else {
            h.respondError(w, http.StatusInternalServerError, "INTERNAL_ERROR", "Failed to fetch shipment", err)
        }
        return
    }

    response := dto.ShipmentToResponse(shipment)
    h.respondSuccess(w, http.StatusOK, response)
}

// UpdateStatus handles POST /api/shipments/:id/status
func (h *ShipmentHandler) UpdateStatus(w http.ResponseWriter, r *http.Request) {
    shipmentID := chi.URLParam(r, "id")
    userID := r.Context().Value("user_id").(string)

    var req dto.UpdateShipmentStatusRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        h.respondError(w, http.StatusBadRequest, "INVALID_REQUEST", "Invalid request body", err)
        return
    }

    status := model.ShipmentLifecycle(req.Status)
    err := h.shipmentService.UpdateShipmentStatus(r.Context(), shipmentID, status, userID)
    if err != nil {
        h.respondError(w, http.StatusBadRequest, "INVALID_STATUS", err.Error(), nil)
        return
    }

    h.respondSuccess(w, http.StatusOK, map[string]string{
        "message": "Status updated successfully",
    })
}

// Helper methods
func (h *ShipmentHandler) validate(req dto.CreateShipmentRequest) error {
    if req.ClientID == "" {
        return errors.New("client_id is required")
    }
    if req.FromStation == "" {
        return errors.New("from_station is required")
    }
    if req.ToStation == "" {
        return errors.New("to_station is required")
    }
    return nil
}

func (h *ShipmentHandler) respondSuccess(w http.ResponseWriter, statusCode int, data interface{}) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(statusCode)
    json.NewEncoder(w).Encode(data)
}

func (h *ShipmentHandler) respondError(w http.ResponseWriter, statusCode int, code, message string, err error) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(statusCode)

    response := dto.ErrorResponse{
        Code:    code,
        Message: message,
    }

    if err != nil {
        h.logger.Error(message, err)
    }

    json.NewEncoder(w).Encode(response)
}
```

## Example 3: PostgreSQL Adapter (Outgoing)

```go
// internal/storage/postgres/shipment_repository.go
package postgres

import (
    "context"
    "database/sql"
    "errors"

    "cargo/backend/internal/domain/ports"
    "cargo/backend/internal/model"
)

type ShipmentRepository struct {
    db *sql.DB
}

func NewShipmentRepository(db *sql.DB) *ShipmentRepository {
    return &ShipmentRepository{db: db}
}

func (r *ShipmentRepository) CreateShipment(ctx context.Context, shipment *model.Shipment) (*model.Shipment, error) {
    query := `
        INSERT INTO shipments (
            id, shipment_number, client_id, client_name, client_email,
            from_station, to_station, current_station, route,
            status, shipment_status, payment_status, 
            weight, dimensions, description, value, cost,
            quantity_places, created_at, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
        ) RETURNING id, created_at, updated_at
    `

    err := r.db.QueryRowContext(ctx, query,
        shipment.ID, shipment.ShipmentNumber, shipment.ClientID, 
        shipment.ClientName, shipment.ClientEmail,
        shipment.FromStation, shipment.ToStation, shipment.CurrentStation,
        pq.Array(shipment.Route), shipment.Status, shipment.ShipmentStatus,
        shipment.PaymentStatus, shipment.Weight, shipment.Dimensions,
        shipment.Description, shipment.Value, shipment.Cost,
        shipment.QuantityPlaces, shipment.CreatedAt, shipment.UpdatedAt,
    ).Scan(&shipment.ID, &shipment.CreatedAt, &shipment.UpdatedAt)

    if err != nil {
        return nil, err
    }

    return shipment, nil
}

func (r *ShipmentRepository) GetShipmentByID(ctx context.Context, id string) (*model.Shipment, error) {
    query := `
        SELECT id, shipment_number, client_id, client_name, client_email,
               from_station, to_station, current_station, next_station, route,
               status, shipment_status, payment_status,
               departure_date, weight, dimensions, description, value, cost,
               quantity_places, receiver_name, receiver_phone,
               train_time, tracking_code, qr_code_id, transport_unit_id,
               last_updated_at, created_by, created_at, updated_at
        FROM shipments WHERE id = $1
    `

    shipment := &model.Shipment{}
    var nextStation, createdBy sql.NullString

    err := r.db.QueryRowContext(ctx, query, id).Scan(
        &shipment.ID, &shipment.ShipmentNumber, &shipment.ClientID,
        &shipment.ClientName, &shipment.ClientEmail,
        &shipment.FromStation, &shipment.ToStation, &shipment.CurrentStation,
        &nextStation, pq.Array(&shipment.Route),
        &shipment.Status, &shipment.ShipmentStatus, &shipment.PaymentStatus,
        &shipment.DepartureDate, &shipment.Weight, &shipment.Dimensions,
        &shipment.Description, &shipment.Value, &shipment.Cost,
        &shipment.QuantityPlaces, &shipment.ReceiverName, &shipment.ReceiverPhone,
        &shipment.TrainTime, &shipment.TrackingCode, &shipment.QRCodeID,
        &shipment.TransportUnitID, &shipment.LastUpdatedAt, &createdBy,
        &shipment.CreatedAt, &shipment.UpdatedAt,
    )

    if err == sql.ErrNoRows {
        return nil, ports.ErrShipmentNotFound
    }
    if err != nil {
        return nil, err
    }

    if nextStation.Valid {
        shipment.NextStation = &nextStation.String
    }
    if createdBy.Valid {
        shipment.CreatedBy = &createdBy.String
    }

    return shipment, nil
}

func (r *ShipmentRepository) UpdateShipment(ctx context.Context, shipment *model.Shipment) (*model.Shipment, error) {
    query := `
        UPDATE shipments SET
            status = $2, shipment_status = $3, payment_status = $4,
            current_station = $5, next_station = $6, route = $7,
            tracking_code = $8, qr_code_id = $9, transport_unit_id = $10,
            last_updated_at = $11, updated_at = $12
        WHERE id = $1
        RETURNING updated_at
    `

    err := r.db.QueryRowContext(ctx, query,
        shipment.ID, shipment.Status, shipment.ShipmentStatus,
        shipment.PaymentStatus, shipment.CurrentStation, shipment.NextStation,
        pq.Array(shipment.Route), shipment.TrackingCode, shipment.QRCodeID,
        shipment.TransportUnitID, shipment.LastUpdatedAt, time.Now(),
    ).Scan(&shipment.UpdatedAt)

    if err == sql.ErrNoRows {
        return nil, ports.ErrShipmentNotFound
    }
    return shipment, err
}

func (r *ShipmentRepository) AddShipmentHistory(ctx context.Context, history *model.ShipmentHistory) error {
    query := `
        INSERT INTO shipment_history (
            shipment_id, action, operator_id, operator_name, station,
            details, old_status, new_status, reason, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    `

    _, err := r.db.ExecContext(ctx, query,
        history.ShipmentID, history.Action, history.OperatorID,
        history.OperatorName, history.Station, history.Details,
        history.OldStatus, history.NewStatus, history.Reason, history.CreatedAt,
    )

    return err
}
```

## Example 4: Dependency Injection & Wiring

```go
// internal/bootstrap/container.go
package bootstrap

import (
    "database/sql"

    "cargo/backend/internal/config"
    "cargo/backend/internal/domain/ports"
    "cargo/backend/internal/domain/service"
    "cargo/backend/internal/notification"
    "cargo/backend/internal/event"
    "cargo/backend/internal/logging"
    "cargo/backend/internal/storage/postgres"
)

type Container struct {
    DB *sql.DB

    // Repositories
    ShipmentRepository ports.ShipmentRepository
    PaymentRepository  ports.PaymentRepository
    UserRepository     ports.UserRepository

    // Ports
    NotificationPort ports.NotificationPort
    EventPublisher   ports.EventPublisher
    Logger           ports.Logger

    // Services
    ShipmentService service.ShipmentService
    PaymentService  service.PaymentService
}

func NewContainer(cfg *config.Config) (*Container, error) {
    c := &Container{}

    // 1. Initialize database
    db, err := setupDatabase(cfg)
    if err != nil {
        return nil, err
    }
    c.DB = db

    // 2. Initialize repositories
    c.ShipmentRepository = postgres.NewShipmentRepository(db)
    c.PaymentRepository = postgres.NewPaymentRepository(db)
    c.UserRepository = postgres.NewUserRepository(db)

    // 3. Initialize external adapters
    c.NotificationPort = notification.NewEmailAdapter(cfg.EmailConfig)
    c.EventPublisher = event.NewKafkaPublisher(cfg.KafkaConfig)
    c.Logger = logging.NewConsoleLogger()

    // 4. Initialize domain services
    c.ShipmentService = service.NewShipmentService(
        c.ShipmentRepository,
        c.EventPublisher,
        c.Logger,
    )

    c.PaymentService = service.NewPaymentService(
        c.PaymentRepository,
        c.NotificationPort,
        c.Logger,
    )

    return c, nil
}

func setupDatabase(cfg *config.Config) (*sql.DB, error) {
    db, err := sql.Open("postgres", cfg.DatabaseURL)
    if err != nil {
        return nil, err
    }

    db.SetMaxOpenConns(25)
    db.SetMaxIdleConns(5)

    if err := db.Ping(); err != nil {
        return nil, err
    }

    return db, nil
}

// Close gracefully closes all resources
func (c *Container) Close() error {
    if c.DB != nil {
        return c.DB.Close()
    }
    return nil
}
```

## Testing Pattern

```go
// shipment_service_test.go
package service

import (
    "context"
    "testing"

    "cargo/backend/internal/model"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
)

// Mock Repository
type MockShipmentRepository struct {
    mock.Mock
}

func (m *MockShipmentRepository) CreateShipment(ctx context.Context, s *model.Shipment) (*model.Shipment, error) {
    args := m.Called(ctx, s)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*model.Shipment), args.Error(1)
}

// Mock Event Publisher
type MockEventPublisher struct {
    mock.Mock
}

func (m *MockEventPublisher) PublishShipmentCreated(ctx context.Context, id string, s *model.Shipment) error {
    return m.Called(ctx, id, s).Error(0)
}

// Test
func TestCreateShipment(t *testing.T) {
    // Arrange
    mockRepo := new(MockShipmentRepository)
    mockPublisher := new(MockEventPublisher)
    mockLogger := new(MockLogger)

    shipment := &model.Shipment{
        ClientID:    "client-1",
        FromStation: "NYC",
        ToStation:   "LA",
    }

    mockRepo.On("CreateShipment", mock.Anything, mock.MatchedBy(func(s *model.Shipment) bool {
        return s.ClientID == "client-1"
    })).Return(shipment, nil)

    mockPublisher.On("PublishShipmentCreated", mock.Anything, mock.Anything, mock.Anything).Return(nil)

    service := NewShipmentService(mockRepo, mockPublisher, mockLogger)

    // Act
    result, err := service.CreateShipment(context.Background(), shipment)

    // Assert
    assert.NoError(t, err)
    assert.NotNil(t, result)
    mockRepo.AssertExpectations(t)
    mockPublisher.AssertExpectations(t)
}
```

---

These examples show how to properly implement hexagonal architecture where each layer has clear responsibilities and can be tested independently.
