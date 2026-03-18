# Hexagonal Architecture - Quick Start Reference

## What We've Created

### 1. Port Interfaces (Core Contracts)
Location: `internal/domain/ports/`

```
📁 ports/
├── logger.go                  → Logger interface
├── shipment_repository.go     → ShipmentRepository interface
├── payment_repository.go      → PaymentRepository interface
├── user_repository.go         → UserRepository interface
├── station_repository.go      → StationRepository interface
├── notification_port.go       → NotificationPort interface
└── event_publisher.go         → EventPublisher interface
```

**What are ports?** They're interfaces that define what adapters must implement. They're the "contracts" between core and external world.

### 2. Domain Events
Location: `internal/domain/events/`

```
📁 events/
└── domain_events.go
    ├── ShipmentCreatedEvent
    ├── ShipmentStatusChangedEvent
    └── PaymentConfirmedEvent
```

**When to use?** When something important happens (shipment created, payment confirmed). Other services can react to these events.

### 3. DTOs (Data Transfer Objects)
Location: `internal/api/dto/`

```
📁 dto/
├── shipment_dto.go     → CreateShipmentRequest, ShipmentResponse, etc.
├── payment_dto.go      → CreatePaymentRequest, PaymentResponse, etc.
├── user_dto.go         → CreateUserRequest, UserResponse, etc.
├── station_dto.go      → CreateStationRequest, StationResponse, etc.
└── common_dto.go       → ErrorResponse, SuccessResponse, Mappers
```

**Why DTOs?** 
- Separate API contract from domain model
- Validate input at boundary
- Can change internal models without breaking API
- Hide internal details

### 4. Adapter Implementations
Location: `internal/[adapter_type]/`

```
📁 logging/
└── console_logger.go         → ConsoleLogger (Logger implementation)

📁 event/
└── mock_publisher.go         → MockEventPublisher (EventPublisher implementation)

📁 notification/
└── mock_adapter.go           → MockNotificationAdapter (NotificationPort implementation)
```

**Purpose:** Implement the port interfaces in different ways (console logging, web services, databases, etc.)

### 5. Bootstrap Container (Dependency Injection)
Location: `internal/bootstrap/`

```
📁 bootstrap/
└── container.go → Wires everything together
```

**What does it do?** Creates all dependencies and injects them into services. Makes testing easier.

---

## The Flow (How It Works)

```
HTTP Request
    ↓
Handler (in api/handlers/)
    ↓
Convert DTO to Domain Model
    ↓
Call Service (in domain/service/)
    ↓
Service uses Repository Port (interface)
    ↓
Repository Adapter (PostgreSQL) implements the port
    ↓
Query Database
    ↓
Return Response → Convert to DTO → HTTP Response
```

**Key:** Each layer only knows about the interfaces (ports), not the implementations!

---

## Current Status: 60% Complete

### ✅ Done
- Ports defined
- DTOs created
- Adapters (logger, event publisher, notification)
- Bootstrap container structure

### ❌ Still Need To Do (In Order)

#### Step 1: Move existing code to new structure
```
OLD: internal/storage/postgres/postgres.go (one large file)

NEW: internal/storage/postgres/repositories/
     ├── shipment_repository.go
     ├── payment_repository.go
     ├── user_repository.go
     └── station_repository.go
```

**Action:** Copy query logic from `postgres.go`, split into separate files, make each satisfy a port interface.

#### Step 2: Create mappers
In `internal/api/dto/common_dto.go`, implement:
```go
func ShipmentToResponse(s *model.Shipment) *ShipmentResponse { ... }
func PaymentToResponse(p *model.Payment) *PaymentResponse { ... }
func UserToResponse(u *model.User) *UserResponse { ... }
func StationToResponse(st *model.Station) *StationResponse { ... }
```

#### Step 3: Create domain services
New files in `internal/domain/service/`:
```
├── shipment_service.go      → Business logic for shipments
├── payment_service.go       → Business logic for payments
├── user_service.go          → Business logic for users
└── station_service.go       → Business logic for stations
```

Each service receives ports (interfaces) via constructor:
```go
func NewShipmentService(
    repo ports.ShipmentRepository,
    eventPub ports.EventPublisher,
    logger ports.Logger,
) *ShipmentService { ... }
```

#### Step 4: Refactor handlers
Update existing handlers in `internal/api/handlers/` to:

**BEFORE:**
```go
func (s *Server) handleCreateShipment(w http.ResponseWriter, r *http.Request) {
    var shipment model.Shipment
    json.NewDecoder(r.Body).Decode(&shipment)
    result, _ := s.repo.CreateShipment(r.Context(), &shipment)
    json.NewEncoder(w).Encode(result)
}
```

**AFTER:**
```go
type ShipmentHandler struct {
    shipmentService *service.ShipmentService
    logger ports.Logger
}

func (h *ShipmentHandler) CreateShipment(w http.ResponseWriter, r *http.Request) {
    var req dto.CreateShipmentRequest
    json.NewDecoder(r.Body).Decode(&req)
    
    // Validate
    if err := h.validate(req); err != nil {
        respondError(w, err)
        return
    }
    
    // Convert to domain model
    shipment := &model.Shipment{
        ClientID: req.ClientID,
        // ...
    }
    
    // Use service
    created, err := h.shipmentService.CreateShipment(r.Context(), shipment)
    if err != nil {
        respondError(w, err)
        return
    }
    
    // Convert to response DTO
    response := dto.ShipmentToResponse(created)
    respondSuccess(w, http.StatusCreated, response)
}
```

#### Step 5: Update container
In `internal/bootstrap/container.go`, initialize repositories:
```go
container.ShipmentRepo = postgres.NewShipmentRepository(db)
container.PaymentRepo = postgres.NewPaymentRepository(db)
container.UserRepo = postgres.NewUserRepository(db)
container.StationRepo = postgres.NewStationRepository(db)
```

#### Step 6: Update main.go
At startup, use container to create services:
```go
func main() {
    container, _ := bootstrap.NewContainer(cfg)
    
    shipmentService := service.NewShipmentService(
        container.ShipmentRepo,
        container.EventPublisher,
        container.Logger,
    )
    
    shipmentHandler := handlers.NewShipmentHandler(shipmentService, container.Logger)
    // ... setup routes
}
```

---

## Testing Before & After

### Before (Hard to test)
```go
// Depends on real database
func TestCreateShipment(t *testing.T) {
    server := NewServer(realDB) // ❌ Requires database
    // Hard to mock, hard to test
}
```

### After (Easy to test)
```go
// Mock everything
func TestCreateShipment(t *testing.T) {
    mockRepo := new(MockShipmentRepository)
    mockEvent := new(MockEventPublisher)
    mockLogger := new(MockLogger)
    
    mockRepo.On("CreateShipment", mock.Anything, mock.Anything).Return(&model.Shipment{...}, nil)
    
    service := service.NewShipmentService(mockRepo, mockEvent, mockLogger)
    
    result, err := service.CreateShipment(context.Background(), &model.Shipment{...})
    
    assert.NoError(t, err)
    mockRepo.AssertExpectations(t) // ✅ Easy to verify
}
```

---

## File Organization Summary

```
backend/
├── cmd/server/main.go              ← Update: use container
├── internal/
│   ├── api/
│   │   ├── handlers/               ← Refactor: use services + DTOs
│   │   ├── dto/                    ✅ CREATED (all DTOs)
│   │   └── server.go               ← Keep existing
│   ├── domain/
│   │   ├── ports/                  ✅ CREATED (all interfaces)
│   │   ├── events/                 ✅ CREATED (domain events)
│   │   └── service/                ← CREATE (business logic)
│   ├── model/
│   │   └── model.go                ← Keep existing
│   ├── storage/
│   │   ├── postgres/
│   │   │   ├── postgres.go         ← Refactor: split into repos
│   │   │   └── repositories/       ← CREATE (separate adapters)
│   │   └── memory/                 ← Optional: for testing
│   ├── event/
│   │   └── mock_publisher.go       ✅ CREATED
│   ├── notification/
│   │   └── mock_adapter.go         ✅ CREATED
│   ├── logging/
│   │   └── console_logger.go       ✅ CREATED
│   ├── bootstrap/
│   │   └── container.go            ✅ CREATED
│   └── config/
│       └── config.go               ← Keep existing
└── go.mod
```

✅ = Ready to use  
← = Update needed
← CREATE = New files to create

---

## Checklist for Completion

- [ ] Create repos in `storage/postgres/repositories/`
- [ ] Implement repo interfaces (ShipmentRepository, etc.)
- [ ] Implement DTO mappers
- [ ] Create domain services (ShipmentService, PaymentService, etc.)
- [ ] Create ShipmentHandler using new pattern
- [ ] Create PaymentHandler using new pattern
- [ ] Create UserHandler using new pattern
- [ ] Create StationHandler using new pattern
- [ ] Update container to initialize all repos
- [ ] Update server.go to use container + new handlers
- [ ] Update main.go to use container
- [ ] Test all endpoints
- [ ] Add real email adapter (replace mock)
- [ ] Add real event publisher (replace mock)
- [ ] Write unit tests for services
- [ ] Write integration tests

---

## Need Help?

**Question:** Where to start?
**Answer:** Start with Step 1 - Move postgres code to separate repository files

**Question:** Do I have to do everything?
**Answer:** No. Do it gradually. Complete one handler at a time.

**Question:** What if I make a mistake?
**Answer:** Easy! Mismatch between port interface and implementation = compile error. Go compiler helps find problems.

