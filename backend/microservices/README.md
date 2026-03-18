# CargoTrans Microservices Architecture

Распределенная архитектура доставки грузов на основе микросервисов, реализованная на Go с использованием паттерна Hexagonal Architecture (Ports & Adapters).

## Обзор архитектуры

Система разделена на 8 независимых микросервисов, каждый отвечающий за отдельный бизнес-домен:

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway / Router                     │
└─────────────────────────────────────────────────────────────┘
         │                 │                │                 │
         ▼                 ▼                ▼                 ▼
    ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ Auth Service│  │Shipment Svc  │  │Payment Svc   │  │Tracking Svc  │
    │ (Port 8001) │  │ (Port 8002)  │  │ (Port 8003)  │  │ (Port 8004)  │
    └─────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
         │                 │                │                 │
         ▼                 ▼                ▼                 ▼
    ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │Notification │  │ Reference    │  │  Audit       │  │   Report     │
    │ Svc (8005) │  │ Svc (8006)   │  │ Svc (8007)   │  │ Svc (8008)   │
    └─────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
         │                 │                │                 │
         └──────────────────┼────────────────┼────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
    ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
    │  PostgreSQL │  │    Redis     │  │  File System │
    └─────────────┘  └──────────────┘  └──────────────┘
```

## Микросервисы

### 1. Auth Service (Port 8001)
Управление аутентификацией, авторизацией и пользователями.

**Функции:**
- Регистрация и вход пользователей
- Управление JWT токенами
- Управление сотрудниками
- Управление корпоративными клиентами
- Управление ролями и правами доступа

**API**: `/auth`, `/admin`, `/clients`

### 2. Shipment Service (Port 8002)
Управление жизненным циклом отправлений.

**Функции:**
- Создание и редактирование отправлений
- Управление 14 статусами доставки
- Расчет тарифов
- Отслеживание маршрутов
- Управление претензиями

**API**: `/shipments`

### 3. Payment Service (Port 8003)
Управление платежами и финансовыми операциями.

**Функции:**
- Создание и подтверждение платежей
- Синхронизация со статусом отправлений
- Логирование аудита платежей

**API**: `/payments`

### 4. Tracking Service (Port 8004)
Отслеживание доставки по QR codам и сканированиям.

**Функции:**
- Генерация QR кодов
- Регистрация сканирований на станциях
- История доставки

**API**: `/tracking`

### 5. Notification Service (Port 8005)
Управление уведомлениями пользователям.

**Функции:**
- Получение уведомлений
- Отметить как прочитанное

**API**: `/notifications`

### 6. Reference Service (Port 8006)
Справочные данные системы.

**Функции:**
- Список ролей
- Управление станциями

**API**: `/roles`, `/stations`

### 7. Audit Service (Port 8007)
Логирование и аудит действий.

**Функции:**
- История изменений
- Фильтрация по типу и действию

**API**: `/audit`

### 8. Report Service (Port 8008)
Аналитика и отчеты.

**Функции:**
- Панель управления
- Финансовые отчеты
- Сводки по статусам

**API**: `/reports`

## Архитектура микросервиса

Каждый микросервис следует паттерну Hexagonal Architecture:

```
service-name/
├── adapters/                          # Адаптеры (слой интеграции)
│   ├── operator/
│   │   └── handle/                   # HTTP handlers
│   │       ├── {service}_handler.go
│   │       ├── middleware.go
│   │       └── router.go
│   └── service/
│       └── database/                 # Database adapters
│           ├── postgres.go
│           └── errors.go
├── core/                             # Ядро приложения
│   ├── domain/                       # Бизнес-логика
│   │   ├── models/                   # Модели данных
│   │   │   └── model.go
│   │   ├── data/                     # DTOs
│   │   │   └── dto.go
│   │   └── services/                 # Бизнес-сервисы
│   │       ├── {service}.go
│   │       ├── types.go
│   │       └── helpers.go
│   ├── ports/                        # Интерфейсы (контракты)
│   │   └── repository.go
│   └── services/                     # Основные сервисы
│       └── {service}_service.go
├── internal/
│   ├── config/
│   │   └── config.go
│   └── middleware/
│       └── auth.go
├── cmd/
│   └── server/
│       └── main.go
├── go.mod
├── go.sum
├── Dockerfile
└── README.md
```

## Развертывание

### Docker Compose

```bash
cd microservices
docker-compose up -d
```

Это запустит все микросервисы, PostgreSQL и Redis.

### Локальное развертывание

1. **Требования:**
   - Go 1.22+
   - PostgreSQL 15+
   - Redis 7+

2. **Запуск каждого сервиса:**

```bash
# Auth Service
cd auth-service
go run ./cmd/server/main.go

# Shipment Service
cd shipment-service
go run ./cmd/server/main.go

# И так далее...
```

## Конфигурация

Каждый микросервис использует переменные окружения для конфигурации:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=cargotrans
DB_PASSWORD=cargotrans_password
DB_NAME=cargotrans_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Auth Service specific
JWT_SECRET=your_jwt_secret_key_here
AUTH_SERVICE_PORT=8001
```

## Порты

| Сервис | Порт |
|--------|------|
| Auth Service | 8001 |
| Shipment Service | 8002 |
| Payment Service | 8003 |
| Tracking Service | 8004 |
| Notification Service | 8005 |
| Reference Service | 8006 |
| Audit Service | 8007 |
| Report Service | 8008 |

## Базы данных

### PostgreSQL

Хост: `localhost:5432`
Пользователь: `cargotrans`
Пароль: `cargotrans_password`
База: `cargotrans_db`

Миграции находятся в `/migrations`

### Redis

Хост: `localhost:6379`
База данных: `0`

## Интеграция между сервисами

Микросервисы взаимодействуют через:

1. **HTTP API** - синхронное взаимодействие
2. **gRPC** (планируется) - асинхронное взаимодействие
3. **Events** (планируется) - событийная архитектура

## Примеры API

### Регистрация пользователя
```bash
POST http://localhost:8001/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe"
}
```

### Создание отправления
```bash
POST http://localhost:8002/shipments
Content-Type: application/json
Authorization: Bearer <token>

{
  "sender_id": "user123",
  "receiver_id": "user456",
  "origin_station": "Шымкент",
  "destination_station": "Алматы-1",
  "description": "Package contents",
  "weight": 5.5,
  "value": 10000.00
}
```

## Тестирование

Postman коллекция находится в `/postman`:
- `CargoTrans.postman_collection.json`
- `cargotrans.postman_environment.json`

## Структура жизненного цикла отправления

```
DRAFT → CREATED → PAYMENT_PENDING → PAID → READY_FOR_LOADING →
LOADED → IN_TRANSIT → ARRIVED → READY_FOR_ISSUE → ISSUED → CLOSED

Варианты ошибок:
→ CANCELLED (отмена)
→ ON_HOLD (удержание)
→ DAMAGED (повреждение)
```

## Логирование

Логи каждого сервиса выводятся в консоль при запуске.

## Мониторинг

Рекомендуется использовать:
- **Prometheus** для метрик
- **ELK Stack** для логов
- **Jaeger** для трассировки

## Безопасность

- JWT токены с подписью
- HTTPS в production
- SQL injection protection (подготовленные запросы)
- Rate limiting (планируется)
- API key authentication (планируется)

## Дальнейшее развитие

- [ ] gRPC для межсервисного взаимодействия
- [ ] Event-driven архитектура
- [ ] API Gateway (Kong/Traefik)
- [ ] Service mesh (Istio)
- [ ] Kubernetes deployment
- [ ] GraphQL API
- [ ] WebSocket для real-time updates
- [ ] Advanced caching strategy
- [ ] Circuit breaker pattern

## Лицензия

MIT

## Контакты

Для вопросов и поддержки, пожалуйста, свяжитесь с командой разработки.
