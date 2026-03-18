# Hexagonal Architecture Implementation Progress

## ✅ COMPLETED

### Layer 1: Domain Layer (Core)
- ✅ `internal/domain/ports/` - All port interfaces defined:
  - `logger.go` - Logger interface
  - `shipment_repository.go` - ShipmentRepository interface
  - `payment_repository.go` - PaymentRepository interface
  - `user_repository.go` - UserRepository interface
  - `station_repository.go` - StationRepository interface
  - `notification_port.go` - NotificationPort interface
  - `event_publisher.go` - EventPublisher interface

- ✅ `internal/domain/events/` - Domain events defined:
  - `domain_events.go` - ShipmentCreatedEvent, ShipmentStatusChangedEvent, PaymentConfirmedEvent

### Layer 2: API / DTO Layer (Boundary)
- ✅ `internal/api/dto/` - All DTOs created:
  - `shipment_dto.go` - Shipment request/response DTOs
  - `payment_dto.go` - Payment request/response DTOs
  - `user_dto.go` - User request/response DTOs
  - `station_dto.go` - Station request/response DTOs
  - `common_dto.go` - Error/Success response DTOs + Mappers (empty stubs)

### Layer 3: Adapters
- ✅ `internal/logging/console_logger.go` - Console logger implementation
- ✅ `internal/event/mock_publisher.go` - Mock event publisher (for development)
- ✅ `internal/notification/mock_adapter.go` - Mock notification adapter (for development)

### Layer 4: Bootstrap (Dependency Injection)
- ✅ `internal/bootstrap/container.go` - Dependency injection container created

---

## ❌ TODO - Step by Step Implementation

### STEP 1: Create Repository Adapter Implementations (Priority: HIGH)

**Location:** `internal/storage/postgres/repositories/`

You need to implement adapters that satisfy your port interfaces. This means refactoring your existing 
`storage/postgres/postgres.go` code into separate repository files:

```go
// CREATE: internal/storage/postgres/repositories/shipment_repository.go
type PostgresShipmentRepository struct {
    db *sql.DB
}

// Implement all methods from ShipmentRepository interface:
func (r *PostgresShipmentRepository) CreateShipment(ctx context.Context, shipment *model.Shipment) (*model.Shipment, error) {
    // Your existing code from postgres.go
}

func (r *PostgresShipmentRepository) GetShipmentByID(ctx context.Context, id string) (*model.Shipment, error) {
    // Your existing code
}
// ... etc

// Same for:
// - payment_repository.go
// - user_repository.go  
// - station_repository.go
```

**Why separate files?**
- Each repository has ONE responsibility
- Easier to test
- Follows Single Responsibility Principle

### STEP 2: Implement DTO Mappers

**Location:** `internal/api/dto/common_dto.go`

Update the mapper functions that convert domain models to response DTOs:

```go
// Before (stub):
func ShipmentToResponse(shipment *interface{}) *ShipmentResponse {
    return &ShipmentResponse{}
}

// After (real):
func ShipmentToResponse(shipment *model.Shipment) *ShipmentResponse {
    return &ShipmentResponse{
        ID:             shipment.ID,
        ShipmentNumber: shipment.ShipmentNumber,
        ClientID:       shipment.ClientID,
        // ... map all fields
    }
}
```

Create similar mappers for:
- `PaymentToResponse()`
- `UserToResponse()`
- `StationToResponse()`

### STEP 3: Create Domain Services

**Location:** `internal/domain/service/`

Create service layers that use ports instead of direct dependencies:

```go
// CREATE: internal/domain/service/shipment_service.go
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

func (s *ShipmentService) CreateShipment(ctx context.Context, shipment *model.Shipment) (*model.Shipment, error) {
    // Validate
    if err := s.validateShipment(shipment); err != nil {
        s.logger.Error(ctx, "invalid shipment", err)
        return nil, err
    }
    
    // Generate tracking code/number if needed
    shipment.TrackingCode = generateTrackingCode()
    
    // Create in repository
    created, err := s.repo.CreateShipment(ctx, shipment)
    if err != nil {
        s.logger.Error(ctx, "failed to create shipment", err)
        return nil, err
    }
    
    // Publish event
    if err := s.eventPublisher.PublishShipmentCreated(ctx, created.ID); err != nil {
        s.logger.Error(ctx, "failed to publish event", err)
        // Don't fail request, but log it
    }
    
    s.logger.Info(ctx, "shipment created", "id", created.ID)
    return created, nil
}

// Similar for: PaymentService, UserService, etc.
```

### STEP 4: Refactor API Handlers to Use DTOs

**Location:** `internal/api/handlers/`

Update existing handlers to:
1. Use DTOs for input/output
2. Use services instead of repositories directly
3. Handle validation at the boundary

```go
// BEFORE (current):
func (s *Server) handleCreateShipment(w http.ResponseWriter, r *http.Request) {
    var shipment model.Shipment
    json.NewDecoder(r.Body).Decode(&shipment)
    
    // direct repo call
    result, err := s.repo.CreateShipment(r.Context(), &shipment)
    // ...
}

// AFTER (new):
func (h *ShipmentHandler) CreateShipment(w http.ResponseWriter, r *http.Request) {
    var req dto.CreateShipmentRequest
    
    // Parse DTO
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        respondError(w, http.StatusBadRequest, "INVALID_REQUEST", err.Error())
        return
    }
    
    // Validate
    if err := h.validateCreateRequest(req); err != nil {
        respondError(w, http.StatusBadRequest, "VALIDATION_ERROR", err.Error())
        return
    }
    
    // Convert DTO to domain model
    shipment := &model.Shipment{
        ClientID:       req.ClientID,
        FromStation:    req.FromStation,
        ToStation:      req.ToStation,
        // ... more fields
    }
    
    // Call service (not repo directly!)
    created, err := h.shipmentService.CreateShipment(r.Context(), shipment)
    if err != nil {
        respondError(w, http.StatusInternalServerError, "INTERNAL_ERROR", err.Error())
        return
    }
    
    // Convert response to DTO
    response := dto.ShipmentToResponse(created)
    respondSuccess(w, http.StatusCreated, response)
}
```

### STEP 5: Update Container to Initialize All Dependencies

**Location:** `internal/bootstrap/container.go`

```go
// Uncomment and implement:
container.ShipmentRepo = postgres.NewShipmentRepository(db)
container.PaymentRepo = postgres.NewPaymentRepository(db)
container.UserRepo = postgres.NewUserRepository(db)
container.StationRepo = postgres.NewStationRepository(db)
```

### STEP 6: Update main.go to Use Container

**Location:** `cmd/server/main.go`

```go
func main() {
    cfg, err := config.Load()
    if err != nil {
        log.Fatal(err)
    }
    
    // Use container for dependency injection
    container, err := bootstrap.NewContainer(cfg)
    if err != nil {
        log.Fatal(err)
    }
    defer container.Close()
    
    // Initialize services
    shipmentService := service.NewShipmentService(
        container.ShipmentRepo,
        container.EventPublisher,
        container.Logger,
    )
    
    paymentService := service.NewPaymentService(
        container.PaymentRepo,
        container.NotificationPort,
        container.Logger,
    )
    
    // Create handlers
    shipmentHandler := handlers.NewShipmentHandler(shipmentService, container.Logger)
    paymentHandler := handlers.NewPaymentHandler(paymentService, container.Logger)
    
    // ... setup routes and start server
}
```

---

## Implementation Order (Recommended)

1. **Week 1:**
   - [ ] Create repository adapters in `storage/postgres/repositories/`
   - [ ] Implement mapper functions in DTOs
   - [ ] Create domain services

2. **Week 2:**
   - [ ] Refactor handlers to use DTOs and services
   - [ ] Update container initialization
   - [ ] Test all refactored endpoints

3. **Week 3:**
   - [ ] Add real implementations for notifications
   - [ ] Add real implementations for event publishing
   - [ ] Integration testing

4. **Week 4:**
   - [ ] Performance testing
   - [ ] Documentation updates
   - [ ] Code review and cleanup

---

## Testing Strategy

Once refactored, testing becomes much easier:

```go
// Easy unit testing with mocks
func TestCreateShipment(t *testing.T) {
    mockRepo := new(MockShipmentRepository)
    mockPublisher := new(MockEventPublisher)
    mockLogger := new(MockLogger)
    
    mockRepo.On("CreateShipment", mock.Anything, mock.Anything).Return(&model.Shipment{...}, nil)
    mockPublisher.On("PublishShipmentCreated", mock.Anything, mock.Anything).Return(nil)
    
    service := service.NewShipmentService(mockRepo, mockPublisher, mockLogger)
    
    result, err := service.CreateShipment(context.Background(), &model.Shipment{...})
    
    assert.NoError(t, err)
    assert.NotNil(t, result)
}
```

---

## Benefits After Refactoring

✅ **Testability** - Mock any external dependency
✅ **Maintainability** - Clear separation of concerns
✅ **Flexibility** - Swap implementations easily
✅ **Scalability** - Add features without breaking existing code
✅ **Independent** - Core business logic independent from frameworks

---

## Questions & Common Issues

**Q: Where should validation go?**
A: At the boundary (handlers) for input validation (DTOs), and in services for business logic validation

**Q: Do I need to update my database schema?**
A: Not yet - the new architecture works with your current schema. The db improvements come next.

**Q: Can I do this gradually?**
A: Yes! Implement one feature/handler at a time using the new pattern. Old and new can coexist.

**Q: What about existing queries in postgres.go?**
A: Move them to the new repository files, keep the logic exactly the same, just change the structure.

---

## Files Structure After Complete Implementation

```
backend/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── api/
│   │   ├── handlers/              ← Currently have these, will refactor
│   │   │   ├── shipment_handler.go
│   │   │   ├── payment_handler.go
│   │   │   └── ...
│   │   ├── dto/                   ← CREATED
│   │   │   ├── shipment_dto.go
│   │   │   ├── payment_dto.go
│   │   │   └── ...
│   │   └── server.go              ← Refactor to use container
│   ├── domain/                    ← CREATED
│   │   ├── ports/                 ← CREATED (interfaces)
│   │   ├── events/                ← CREATED (domain events)
│   │   └── service/               ← NEW (business logic services)
│   ├── model/                     ← Keep existing
│   │   └── model.go
│   ├── storage/
│   │   ├── postgres/              ← Keep existing logic
│   │   │   ├── postgres.go
│   │   │   └── repositories/      ← NEW (refactored adapters)
│   │   │       ├── shipment_repository.go
│   │   │       ├── payment_repository.go
│   │   │       └── ...
│   │   └── memory/                ← Optional: for testing
│   ├── event/                     ← NEW (outgoing adapter)
│   │   └── mock_publisher.go
│   ├── notification/              ← NEW (outgoing adapter)
│   │   └── mock_adapter.go
│   ├── logging/                   ← NEW (adapter)
│   │   └── console_logger.go
│   ├── config/
│   │   └── config.go
│   └── bootstrap/                 ← NEW (DI container)
│       └── container.go
├── go.mod
├── Dockerfile
└── docker-compose.yml
```

