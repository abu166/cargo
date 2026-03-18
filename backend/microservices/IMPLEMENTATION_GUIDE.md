# Microservices Implementation Guide

## Текущее состояние

Успешно создана основная структура 8 микросервисов с использованием паттерна Hexagonal Architecture (Ports & Adapters).

## Что уже готово ✅

1. **Структура папок** - все необходимые директории созданы
2. **Модели данных** - полная доменная модель для каждого сервиса
3. **DTOs** - запросы и ответы для всех API endpoints
4. **Интерфейсы сервисов** - Repository контракты для каждого сервиса
5. **Бизнес-логика** - основные методы сервисов переведены из монолита
6. **Конфигурация** - загрузка и управление конфигом для каждого сервиса
7. **Middleware** - базовые middleware (логирование, восстановление, CORS)
8. **Docker** - Dockerfile для каждого сервиса и docker-compose.yml для всей системы
9. **Документация** - README для каждого сервиса и главная архитектурная документация

## Следующие шаги

### 1. HTTP Адаптеры (Handlers)

Каждый сервис нуждается в HTTP обработчиках в `adapters/operator/handle/`

**Файлы для создания:**

```
auth-service/adapters/operator/handle/
├── router.go              # Определение маршрутов
├── auth_handler.go        # Обработчики аутентификации
├── admin_handler.go       # Обработчики управления персоналом
└── client_handler.go      # Обработчики корпоративных клиентов

shipment-service/adapters/operator/handle/
├── router.go              # Определение маршрутов
└── shipment_handler.go    # Все обработчики отправлений

payment-service/adapters/operator/handle/
├── router.go              # Определение маршрутов
└── payment_handler.go     # Обработчики платежей

tracking-service/adapters/operator/handle/
├── router.go              # Определение маршрутов
└── tracking_handler.go    # Обработчики отслеживания

notification-service/adapters/operator/handle/
├── router.go              # Определение маршрутов
└── notification_handler.go # Обработчики уведомлений

reference-service/adapters/operator/handle/
├── router.go              # Определение маршрутов
└── reference_handler.go   # Обработчики справочных данных

audit-service/adapters/operator/handle/
├── router.go              # Определение маршрутов
└── audit_handler.go       # Обработчики аудита

report-service/adapters/operator/handle/
├── router.go              # Определение маршрутов
└── report_handler.go      # Обработчики отчетов
```

**Пример структуры handler файла:**

```go
package handle

import (
	"encoding/json"
	"net/http"
	
	"cargo/backend/microservices/auth-service/core/domain/data"
	"cargo/backend/microservices/auth-service/core/services"
)

type AuthHandler struct {
	service services.AuthService
}

func NewAuthHandler(service services.AuthService) *AuthHandler {
	return &AuthHandler{service: service}
}

func (h *AuthHandler) Register(w http.ResponseWriter, r *http.Request) {
	var req data.RegisterRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}
	
	// TODO: Вызвать h.service.Register()
	// TODO: Вернуть response
}

func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	// TODO: Реализовать login handler
}
```

### 2. Database Адаптеры

Каждый сервис нуждается в адаптерах БД в `adapters/service/database/`

**Файлы для создания:**

```
{service}/adapters/service/database/
├── postgres.go            # PostgreSQL адаптер
├── errors.go              # Обработка ошибок БД
└── queries.go             # SQL запросы (опционально)
```

**Пример структуры PostgreSQL адаптера:**

```go
package database

import (
	"context"
	"database/sql"
	
	"cargo/backend/microservices/auth-service/core/domain/models"
	"cargo/backend/microservices/auth-service/core/services"
)

type PostgresRepository struct {
	db *sql.DB
}

func NewPostgresRepository(db *sql.DB) services.Repository {
	return &PostgresRepository{db: db}
}

// Реализовать методы интерфейса Repository
func (r *PostgresRepository) CreateUser(ctx context.Context, user models.User) error {
	// TODO: Реализовать SQL запрос
	return nil
}
```

### 3. Router Определения

Каждый handler должен иметь router.go для регистрации маршрутов

**Пример:**

```go
package handle

import (
	"net/http"
	
	"cargo/backend/microservices/auth-service/core/services"
)

func SetupRoutes(mux *http.ServeMux, authService services.AuthService) {
	handler := NewAuthHandler(authService)
	
	mux.HandleFunc("POST /auth/register", handler.Register)
	mux.HandleFunc("POST /auth/login", handler.Login)
	mux.HandleFunc("GET /auth/me", handler.Me)
	// ... и т.д.
}
```

### 4. Инициализация сервисов в main.go

Каждый `cmd/server/main.go` должен:

1. Подключиться к БД
2. Создать Repository
3. Создать Service с Repository
4. Создать и зарегистрировать Handlers
5. Запустить HTTP сервер

**Пример (auth-service):**

```go
package main

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
	
	_ "github.com/lib/pq"
	
	"cargo/backend/microservices/auth-service/internal/config"
	"cargo/backend/microservices/auth-service/internal/middleware"
	"cargo/backend/microservices/auth-service/adapters/operator/handle"
	"cargo/backend/microservices/auth-service/adapters/service/database"
	"cargo/backend/microservices/auth-service/core/services"
)

func main() {
	cfg := config.LoadConfig()
	
	// Подключиться к БД
	db, err := sql.Open("postgres", getDSN(cfg))
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.Close()
	
	// Создать Repository
	repo := database.NewPostgresRepository(db)
	
	// Создать Service
	authService := services.NewAuthService(repo)
	
	// Создать HTTP сервер
	mux := http.NewServeMux()
	
	// Регистрировать маршруты
	handle.SetupRoutes(mux, authService)
	
	// Применить middleware
	var handler http.Handler = mux
	handler = middleware.CORSMiddleware(handler)
	handler = middleware.RecoveryMiddleware(handler)
	handler = middleware.LoggerMiddleware(handler)
	
	// Запустить сервер
	addr := fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port)
	server := &http.Server{
		Addr:         addr,
		Handler:      handler,
		ReadTimeout:  cfg.Server.ReadTimeout,
		WriteTimeout: cfg.Server.WriteTimeout,
	}
	
	log.Printf("Server listening on %s", addr)
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("Server error: %v", err)
	}
}

func getDSN(cfg *config.Config) string {
	return fmt.Sprintf(
		"user=%s password=%s host=%s port=%d dbname=%s sslmode=%s",
		cfg.Database.User,
		cfg.Database.Password,
		cfg.Database.Host,
		cfg.Database.Port,
		cfg.Database.DBName,
		cfg.Database.SSLMode,
	)
}
```

### 5. Тестирование

После имплементации handlers:

```bash
# Запустить все сервисы
cd microservices
docker-compose up

# Или запустить локально
cd auth-service
go run ./cmd/server/main.go

# Тестировать API с Postman или curl
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

## Рекомендуемый порядок имплементации

1. **Auth Service** - других сервисов зависят от аутентификации
2. **Reference Service** - справочные данные нужны для валидации
3. **Shipment Service** - основной сервис системы
4. **Payment Service** - зависит от Shipment
5. **Tracking Service** - зависит от Shipment
6. **Notification Service** - может быть независим
7. **Audit Service** - логирует события других сервисов
8. **Report Service** - агрегирует данные других сервисов

## Зависимости для каждого сервиса

Убедитесь, что в `go.mod` добавлены все необходимые пакеты:

```go
require (
	github.com/lib/pq v1.10.9              // PostgreSQL driver
	github.com/go-redis/redis/v8 v8.11.0   // Redis client
	github.com/joho/godotenv v1.5.1        // Загрузка .env
	github.com/golang-jwt/jwt/v5 v5.0.0    // JWT (для auth-service)
	github.com/google/uuid v1.3.0          // UUID generator
	golang.org/x/crypto v0.12.0            // Криптография (для auth-service)
)
```

## Миграции БД

Используйте существующие миграции из `/migrations`:

```sql
-- 001_create_tables.up.sql
-- 002_migrate_existing_schema.up.sql
-- 003_test_data.up.sql
```

Примените их при запуске:

```bash
# В docker-compose они применяются автоматически
# Для локальной разработки:
psql -U cargotrans -d cargotrans_db -f migrations/001_create_tables.up.sql
```

## Полезные команды

```bash
# Запустить все сервисы
docker-compose up -d

# Просмотреть логи
docker-compose logs -f auth-service

# Остановить все
docker-compose down

# Пересобрать
docker-compose up --build

# Проверить подключение к БД
psql -U cargotrans -h localhost -d cargotrans_db
```

## Checklist для готовности

- [ ] Все handlers реализованы
- [ ] Все Repository методы реализованы
- [ ] Все маршруты зарегистрированы
- [ ] Конфигурация загружается корректно
- [ ] Middleware применяется правильно
- [ ] Docker images собираются успешно
- [ ] docker-compose запускает все сервисы
- [ ] API endpoints работают как ожидается
- [ ] Аутентификация и авторизация работают
- [ ] Данные сохраняются в БД корректно

## Дальнейшее развитие

После основной имплементации:

1. **gRPC** - для синхронного взаимодействия между сервисами
2. **Event Bus** - для асинхронного взаимодействия (Kafka, RabbitMQ)
3. **API Gateway** - центральная точка входа (Kong, Traefik)
4. **Service Mesh** - управление трафиком между сервисами (Istio)
5. **Unit Tests** - покрытие тестами для критичных функций
6. **Integration Tests** - тестирование взаимодействия сервисов
7. **CI/CD** - автоматизация сборки и развертывания
8. **Monitoring** - Prometheus + Grafana для метрик
9. **Logging** - ELK Stack для централизованных логов
10. **Tracing** - Jaeger для трассировки запросов

## Получнение помощи

Помощь по каждому этапу:
- Свяжитесь с архитектором для вопросов по архитектуре
- Обратитесь к документации Go/PostgreSQL для технических вопросов
- Используйте Postman коллекцию для тестирования API

---

**Последнее обновление:** Версия 1.0 (Foundation Complete)
**Статус:** Готово к имплементации HTTP слоя и Database слоя
