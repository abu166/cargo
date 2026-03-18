.PHONY: help build build-all up down logs clean test migrate docker-build docker-push

# Variables
SERVICES := auth-service shipment-service payment-service tracking-service notification-service reference-service audit-service report-service
DOCKER_REGISTRY ?= your-registry
VERSION ?= latest

# Default target
help:
	@echo "CargoTrans Microservices - Available commands:"
	@echo ""
	@echo "Build & Development:"
	@echo "  make build SERVICE=auth-service          Build a specific service"
	@echo "  make build-all                            Build all services"
	@echo "  make clean                                Remove build artifacts"
	@echo ""
	@echo "Docker:"
	@echo "  make up                                   Start all services with Docker Compose"
	@echo "  make down                                 Stop all services"
	@echo "  make logs SERVICE=auth-service            View service logs"
	@echo "  make docker-build SERVICE=auth-service    Build Docker image for service"
	@echo "  make docker-push SERVICE=auth-service     Push Docker image to registry"
	@echo ""
	@echo "Database:"
	@echo "  make migrate                              Run database migrations"
	@echo "  make migrate-down                         Rollback database migrations"
	@echo ""
	@echo "Testing:"
	@echo "  make test SERVICE=auth-service            Run tests for a service"
	@echo "  make test-all                             Run tests for all services"
	@echo ""
	@echo "Development:"
	@echo "  make run SERVICE=auth-service             Run a service locally"
	@echo "  make run-all                              Run all services locally"
	@echo "  make format                               Format all code"
	@echo "  make lint                                 Lint all code"

# Build targets
build:
	@if [ -z "$(SERVICE)" ]; then \
		echo "Error: SERVICE not specified. Usage: make build SERVICE=auth-service"; \
		exit 1; \
	fi
	@echo "Building $(SERVICE)..."
	cd $(SERVICE) && go build -o bin/$(SERVICE) ./cmd/server/main.go

build-all:
	@echo "Building all services..."
	@for service in $(SERVICES); do \
		echo "Building $$service..."; \
		cd $$service && go build -o bin/$$service ./cmd/server/main.go && cd ..; \
	done
	@echo "All services built successfully!"

clean:
	@echo "Cleaning build artifacts..."
	@for service in $(SERVICES); do \
		rm -rf $$service/bin; \
	done
	@echo "Clean complete!"

# Docker targets
up:
	@echo "Starting all services with Docker Compose..."
	docker-compose up -d
	@echo "Services are running!"
	@echo "Access points:"
	@echo "  Auth Service:         http://localhost:8001"
	@echo "  Shipment Service:     http://localhost:8002"
	@echo "  Payment Service:      http://localhost:8003"
	@echo "  Tracking Service:     http://localhost:8004"
	@echo "  Notification Service: http://localhost:8005"
	@echo "  Reference Service:    http://localhost:8006"
	@echo "  Audit Service:        http://localhost:8007"
	@echo "  Report Service:       http://localhost:8008"

down:
	@echo "Stopping all services..."
	docker-compose down
	@echo "All services stopped!"

logs:
	@if [ -z "$(SERVICE)" ]; then \
		echo "Viewing logs for all services..."; \
		docker-compose logs -f; \
	else \
		echo "Viewing logs for $(SERVICE)..."; \
		docker-compose logs -f $(SERVICE); \
	fi

docker-build:
	@if [ -z "$(SERVICE)" ]; then \
		echo "Error: SERVICE not specified. Usage: make docker-build SERVICE=auth-service"; \
		exit 1; \
	fi
	@echo "Building Docker image for $(SERVICE)..."
	docker build -t $(DOCKER_REGISTRY)/$(SERVICE):$(VERSION) ./$(SERVICE)
	@echo "Docker image built successfully!"

docker-push:
	@if [ -z "$(SERVICE)" ]; then \
		echo "Error: SERVICE not specified. Usage: make docker-push SERVICE=auth-service"; \
		exit 1; \
	fi
	@echo "Pushing Docker image for $(SERVICE)..."
	docker push $(DOCKER_REGISTRY)/$(SERVICE):$(VERSION)
	@echo "Docker image pushed successfully!"

# Database targets
migrate:
	@echo "Running database migrations..."
	@echo "Note: Migrations are applied automatically with docker-compose"
	@echo "For manual migration, run:"
	@echo "  psql -U cargotrans -d cargotrans_db -f migrations/001_create_tables.up.sql"

migrate-down:
	@echo "Rolling back database migrations..."
	@echo "Note: Use the .down.sql files to rollback changes"

# Testing targets
test:
	@if [ -z "$(SERVICE)" ]; then \
		echo "Error: SERVICE not specified. Usage: make test SERVICE=auth-service"; \
		exit 1; \
	fi
	@echo "Running tests for $(SERVICE)..."
	cd $(SERVICE) && go test ./...

test-all:
	@echo "Running tests for all services..."
	@for service in $(SERVICES); do \
		echo "Testing $$service..."; \
		cd $$service && go test ./... || true; \
		cd ..; \
	done
	@echo "All tests completed!"

# Development targets
run:
	@if [ -z "$(SERVICE)" ]; then \
		echo "Error: SERVICE not specified. Usage: make run SERVICE=auth-service"; \
		exit 1; \
	fi
	@echo "Running $(SERVICE) locally..."
	cd $(SERVICE) && go run ./cmd/server/main.go

run-all:
	@echo "Error: Use 'make up' to run all services with Docker Compose"
	@echo "Or run services individually with 'make run SERVICE=service-name'"

format:
	@echo "Formatting code..."
	@for service in $(SERVICES); do \
		cd $$service && go fmt ./... && cd ..; \
	done
	@echo "Code formatting complete!"

lint:
	@echo "Linting code..."
	@for service in $(SERVICES); do \
		echo "Linting $$service..."; \
		cd $$service && golangci-lint run ./... || true; \
		cd ..; \
	done

# Utility targets
ps:
	@echo "Running services:"
	docker-compose ps

restart:
	@echo "Restarting all services..."
	docker-compose restart
	@echo "All services restarted!"

version:
	@echo "CargoTrans Microservices v1.0"
	@echo "Services count: $(words $(SERVICES))"
	@echo "Services: $(SERVICES)"
