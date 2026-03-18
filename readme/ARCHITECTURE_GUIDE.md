# CargoGO Hexagonal Architecture Guide

## Overview

Hexagonal Architecture (also known as Ports & Adapters) organizes code into clearly separated layers, making your application independent of external frameworks and mechanisms. This enables easier testing, maintenance, and evolution.

## Current Architecture Assessment

✅ **What You're Doing Well:**
- Clear separation between `api/`, `service/`, `model/`, and `storage/` layers
- Repository pattern abstraction in `service/repository.go`
- Domain models concentrated in `model/model.go`
- Multiple specialized services (ShipmentService, PaymentService, etc.)

⚠️ **Areas for Improvement:**
- Repository interface should have **separate interfaces** for each domain (ShipmentRepository, PaymentRepository, etc.)
- No explicit DTOs (Data Transfer Objects) for separating API layer from domain models
- Business logic validation should be in domain model methods, not just in services
- Missing Domain Events for important state transitions
- No clear dependency injection container

## Hexagonal Architecture Structure

### Three Main Rings:

#### 1. **Core (Innermost)**
Domain-driven, independent of frameworks.
```
internal/
├── model/          # Domain entities, value objects, aggregates
├── domain/         # Interfaces (ports) & domain events
└── service/        # Business logic & use cases
```

#### 2. **Ports**
Abstractions that define how the core communicates outward/inward.
```
internal/domain/
├── ports/
│   ├── shipment_repo.go     # Interface for shipment storage
│   ├── payment_repo.go      # Interface for payment storage
│   ├── notification_service.go  # Outbound notification port
│   ├── event_publisher.go   # Outbound event publishing
│   └── ...
```

#### 3. **Adapters (Outermost)**
Implement ports and communicate with external systems.
```
internal/
├── api/             # HTTP adapter (incoming)
├── storage/         # Database adapter (outgoing)
├── notification/    # Email/SMS adapter (outgoing)
└── event/           # Message broker adapter (outgoing)
```

## Implementation Steps for CargoGO

### Step 1: Refactor Repository Interface into Domain-Specific Interfaces

**Current (Monolithic):**
```go
// service/repository.go - Too many responsibilities
type Repository interface {
    CreateUser(...)
    CreateShipment(...)
    CreatePayment(...)
    // ... 40+ methods
}
```

**Recommended:**
```go
// internal/domain/ports/shipment_repository.go
type ShipmentRepository interface {
    CreateShipment(ctx context.Context, shipment *model.Shipment) error
    GetShipmentByID(ctx context.Context, id string) (*model.Shipment, error)
    UpdateShipment(ctx context.Context, shipment *model.Shipment) error
    ListShipments(ctx context.Context, filter *model.ShipmentFilter) ([]model.Shipment, error)
}

// internal/domain/ports/payment_repository.go
type PaymentRepository interface {
    CreatePayment(ctx context.Context, payment *model.Payment) error
    GetPayment(ctx context.Context, id string) (*model.Payment, error)
    UpdatePayment(ctx context.Context, payment *model.Payment) error
    ListPaymentsByShipment(ctx context.Context, shipmentID string) ([]model.Payment, error)
}

// Similar for: UserRepository, NotificationRepository, AuditRepository, etc.
```

### Step 2: Create DTO Layer for API Boundary

Create separate request/response models to decouple API from domain:

```go
// internal/api/dto/shipment_dto.go
type CreateShipmentRequest struct {
    ClientID         string   `json:"client_id" validate:"required"`
    FromStation      string   `json:"from_station" validate:"required"`
    ToStation        string   `json:"to_station" validate:"required"`
    Weight           string   `json:"weight" validate:"required"`
    Dimensions       string   `json:"dimensions" validate:"required"`
    // ... other fields
}

type ShipmentResponse struct {
    ID                string            `json:"id"`
    ShipmentNumber    string            `json:"shipment_number"`
    Status            string            `json:"status"`
    ShipmentStatus    string            `json:"shipment_status"`
    // ... only expose relevant fields
}

// Mapper function
func ToShipmentResponse(shipment *model.Shipment) *ShipmentResponse {
    return &ShipmentResponse{
        ID:             shipment.ID,
        ShipmentNumber: shipment.ShipmentNumber,
        // ...
    }
}
```

**Benefits:**
- Hide internal domain details from API clients
- Validate input at API boundary
- Easily version APIs without changing domain model
- Third-party integrations don't depend on your domain

### Step 3: Define Outbound Ports (Integration Points)

```go
// internal/domain/ports/notification_service.go
type NotificationPort interface {
    SendEmail(ctx context.Context, to, subject, body string) error
    SendSMS(ctx context.Context, phone, message string) error
    SendPushNotification(ctx context.Context, userID, message string) error
}

// internal/domain/ports/event_publisher.go
type EventPublisher interface {
    PublishShipmentCreated(ctx context.Context, event *model.ShipmentCreatedEvent) error
    PublishPaymentConfirmed(ctx context.Context, event *model.PaymentConfirmedEvent) error
    PublishShipmentStatusChanged(ctx context.Context, event *model.ShipmentStatusChangedEvent) error
}

// internal/domain/ports/logger.go
type Logger interface {
    Info(msg string, fields ...interface{})
    Error(msg string, err error, fields ...interface{})
    Debug(msg string, fields ...interface{})
}
```

### Step 4: Implement Adapters

```go
// internal/storage/postgres/shipment_repository.go
type PostgresShipmentRepository struct {
    db *sql.DB
}

func (r *PostgresShipmentRepository) CreateShipment(ctx context.Context, s *model.Shipment) error {
    // PostgreSQL implementation
}

// internal/notification/email_adapter.go
type EmailNotificationAdapter struct {
    smtpClient *smtp.Client
    sender     string
}

func (a *EmailNotificationAdapter) SendEmail(ctx context.Context, to, subject, body string) error {
    // Email implementation
}

// internal/event/kafka_publisher.go
type KafkaEventPublisher struct {
    producer kafka.Producer
}

func (p *KafkaEventPublisher) PublishShipmentCreated(ctx context.Context, event *model.ShipmentCreatedEvent) error {
    // Kafka implementation
}
```

### Step 5: Add Domain Events

```go
// internal/domain/events/shipment_events.go
type DomainEvent interface {
    AggregateID() string
    EventType() string
    Timestamp() time.Time
}

type ShipmentCreatedEvent struct {
    aggregateID string
    ShipmentID  string
    ClientID    string
    FromStation string
    ToStation   string
    timestamp   time.Time
}

type ShipmentStatusChangedEvent struct {
    aggregateID  string
    ShipmentID   string
    OldStatus    model.ShipmentLifecycle
    NewStatus    model.ShipmentLifecycle
    ChangedAt    time.Time
    ChangedBy    string
    timestamp    time.Time
}

// Usage in service
func (s *ShipmentService) CreateShipment(ctx context.Context, shipment *model.Shipment) error {
    if err := s.repo.CreateShipment(ctx, shipment); err != nil {
        return err
    }
    
    event := &ShipmentCreatedEvent{
        ShipmentID:  shipment.ID,
        ClientID:    shipment.ClientID,
        FromStation: shipment.FromStation,
        ToStation:   shipment.ToStation,
        timestamp:   time.Now(),
    }
    
    return s.eventPublisher.PublishShipmentCreated(ctx, event)
}
```

### Step 6: Dependency Injection Container

```go
// internal/bootstrap/container.go
type Container struct {
    // Repositories
    ShipmentRepo domain.ShipmentRepository
    PaymentRepo  domain.PaymentRepository
    UserRepo     domain.UserRepository
    
    // Ports
    NotificationPort domain.NotificationPort
    EventPublisher   domain.EventPublisher
    Logger           domain.Logger
    
    // Services
    ShipmentService domain.ShipmentService
    PaymentService  domain.PaymentService
}

func NewContainer(cfg *config.Config) (*Container, error) {
    // Initialize PostgreSQL
    db, err := setupDatabase(cfg)
    if err != nil {
        return nil, err
    }
    
    // Initialize repositories
    shipmentRepo := storage.NewPostgresShipmentRepository(db)
    paymentRepo := storage.NewPostgresPaymentRepository(db)
    userRepo := storage.NewPostgresUserRepository(db)
    
    // Initialize adapters
    notificationAdapter := notification.NewEmailAdapter(cfg.SMTPConfig)
    eventPublisher := event.NewKafkaPublisher(cfg.KafkaConfig)
    logger := logging.NewConsoleLogger()
    
    // Initialize services
    shipmentService := service.NewShipmentService(shipmentRepo, eventPublisher, logger)
    paymentService := service.NewPaymentService(paymentRepo, notificationAdapter, logger)
    
    return &Container{
        ShipmentRepo:     shipmentRepo,
        PaymentRepo:      paymentRepo,
        UserRepo:         userRepo,
        NotificationPort: notificationAdapter,
        EventPublisher:   eventPublisher,
        Logger:           logger,
        ShipmentService:  shipmentService,
        PaymentService:   paymentService,
    }, nil
}
```

### Step 7: Updated Project Structure

```
backend/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── model/           # Domain entities (no external deps)
│   │   └── model.go
│   ├── domain/          # Domain logic & ports (no external deps)
│   │   ├── shipment_service.go
│   │   ├── payment_service.go
│   │   ├── ports/
│   │   │   ├── shipment_repository.go
│   │   │   ├── payment_repository.go
│   │   │   ├── user_repository.go
│   │   │   ├── notification_port.go
│   │   │   ├── event_publisher.go
│   │   │   └── logger.go
│   │   └── events/
│   │       ├── shipment_events.go
│   │       └── payment_events.go
│   ├── api/             # HTTP adapter (incoming)
│   │   ├── server.go
│   │   ├── dto/
│   │   │   ├── shipment_dto.go
│   │   │   ├── payment_dto.go
│   │   │   └── mapper.go
│   │   └── handlers/
│   │       ├── shipment_handler.go
│   │       └── ...
│   ├── storage/         # Data storage adapters (outgoing)
│   │   ├── postgres/
│   │   │   ├── shipment_repository.go
│   │   │   ├── payment_repository.go
│   │   │   └── ...
│   │   └── memory/      # For testing
│   │       └── ...
│   ├── notification/    # Notification adapters (outgoing)
│   │   ├── email_adapter.go
│   │   ├── sms_adapter.go
│   │   └── push_adapter.go
│   ├── event/           # Event publishing adapters (outgoing)
│   │   ├── kafka_publisher.go
│   │   └── mock_publisher.go
│   ├── bootstrap/       # Dependency injection
│   │   └── container.go
│   └── config/
│       └── config.go
├── go.mod
├── Dockerfile
└── docker-compose.yml
```

## Testing Benefits

With hexagonal architecture, testing becomes straightforward:

```go
// test using mock repository
type MockShipmentRepository struct {
    mock.Mock
}

func TestShipmentService_CreateShipment(t *testing.T) {
    mockRepo := new(MockShipmentRepository)
    mockPublisher := new(MockEventPublisher)
    
    mockRepo.On("CreateShipment", mock.Anything, mock.Anything).Return(nil)
    mockPublisher.On("PublishShipmentCreated", mock.Anything, mock.Anything).Return(nil)
    
    service := domain.NewShipmentService(mockRepo, mockPublisher, mockLogger)
    
    shipment := &model.Shipment{
        ClientID:    "client-1",
        FromStation: "NYC",
        ToStation:   "LA",
    }
    
    err := service.CreateShipment(context.Background(), shipment)
    assert.NoError(t, err)
    mockRepo.AssertExpectations(t)
}
```

## Key Principles for CargoGO

1. **Domain entities live in** `model/` and `domain/` - **completely independent**
2. **Ports are interfaces** in `domain/ports/` - **define contracts**
3. **Adapters implement ports** in `api/`, `storage/`, `notification/` - **handle external communication**
4. **Services orchestrate** using ports - **zero direct dependencies on adapters**
5. **DTOs translate** between API and domain - **boundary definitions**
6. **Events notify** of important state changes - **decoupling through events**

## Migration Path

Phase 1: Create domain/ports/ interfaces
Phase 2: Create DTOs for API boundary
Phase 3: Add domain events
Phase 4: Implement dependency injection container
Phase 5: Refactor handlers to use DTOs
Phase 6: Add more specialized adapters (notifications, events)

## Additional Resources

- Clean Architecture by Robert C. Martin
- Domain-Driven Design by Eric Evans
- Ports & Adapters Architecture Pattern

---

This structure ensures your CargoGO backend is:
- ✅ Testable (easy mocking)
- ✅ Maintainable (clear dependencies)
- ✅ Scalable (independent layers)
- ✅ Adaptable (swap implementations easily)
