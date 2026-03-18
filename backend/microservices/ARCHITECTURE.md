# CargoTrans Microservices Architecture

## Обзор

CargoTrans - это распределенная система управления доставкой грузов, построенная на микросервисной архитектуре. Каждый микросервис отвечает за отдельный бизнес-домен и может быть независимо развернут, масштабирован и обновлен.

## Архитектурный паттерн: Hexagonal Architecture (Ports & Adapters)

Каждый микросервис следует паттерну Hexagonal Architecture, обеспечивающему четкое разделение ответственности:

```
┌─────────────────────────────────────────────────────────────────┐
│                      Adapters Layer                              │
│  ┌──────────────────┐                  ┌──────────────────┐    │
│  │  HTTP Handlers   │                  │  Database Driver │    │
│  │   (Operator)     │                  │   (Service)      │    │
│  │  Port: 8xxx      │                  │  (PostgreSQL)    │    │
│  └────────┬─────────┘                  └────────┬─────────┘    │
│           │┌─────────────────────────────────────┤              │
└───────────┼────────────────────────────────────────────────────┘
            │
┌───────────┼────────────────────────────────────────────────────┐
│ ┌─────────▼──────────────┐          ┌──────────────────────┐   │
│ │                        │          │                      │   │
│ │    Domain Logic        │          │    Ports (i/f)       │   │
│ │  (Biz Services)        │◄─────────│   (Contracts)        │   │
│ │                        │          │                      │   │
│ │                        │          │                      │   │
│ │  ┌──────────────────┐  │          │ - Repository         │   │
│ │  │  Models/Entities │  │          │ - EventPublisher     │   │
│ │  │  (Aggregates)    │  │          │ - Notifications      │   │
│ │  └──────────────────┘  │          └──────────────────────┘   │
│ │                        │                                      │
│ │  ┌──────────────────┐  │                                      │
│ │  │   DTOs           │  │                                      │
│ │  │   (Data Trans.)  │  │                                      │
│ │  └──────────────────┘  │                                      │
│ └────────────────────────┘                                      │
│                                                                |
│              Core Domain (Business Rules)                      │
│             Independent of Framework/DB                        │
└────────────────────────────────────────────────────────────────┘
```

### Слои архитектуры

#### 1. **Core Domain** (Ядро)
- **Models** - Доменные модели (Aggregates, Value Objects)
- **Services** - Бизнес-логика, не зависит от фреймворков
- **Ports** - Интерфейсы (контракты) для взаимодействия
- **Data** - DTO (Data Transfer Objects)

Примеры:
```
core/
├── domain/
│   ├── models/       # Shipment, Payment, User, etc.
│   ├── data/         # CreateShipmentRequest, PaymentDTO, etc.
│   └── services/     # ShipmentService, PaymentService, etc.
├── ports/           # Repository interface definitions
└── services/        # Service initialization
```

#### 2. **Adapters** (Адаптеры)
- **Operator Adapter** - Входящий адаптер (HTTP handlers, gRPC servers)
- **Service Adapter** - Исходящий адаптер (Database, Cache, Message Queue)

Примеры:
```
adapters/
├── operator/
│   └── handle/      # HTTP handlers, routes, middleware
└── service/
    └── database/    # PostgreSQL implementation, queries
```

#### 3. **Internal** (Внутренняя конфигурация)
- **Config** - Загрузка и управление конфигурацией
- **Middleware** - Аутентификация, логирование, CORS

## Микросервисы системы

### 1. Auth Service (Port 8001)

**Ответственность:**
- Управление пользователями
- Аутентификация и авторизация
- Выпуск и валидация JWT токенов
- Управление ролями и правами доступа

**Ключевые компоненты:**
- `AuthService` - JWT выпуск, валидация, управление сессиями
- `AdminService` - CRUD операции для сотрудников
- `ClientService` - CRUD операции для корпоративных клиентов

**API:**
```
POST   /auth/register          - Регистрация
POST   /auth/login             - Вход
GET    /auth/me                - Получить текущего пользователя

GET    /admin/employees        - Список сотрудников
POST   /admin/employees        - Создать сотрудника
PUT    /admin/users/:id        - Обновить пользователя
DELETE /admin/employees/:id    - Удалить сотрудника

GET    /clients                - Список клиентов
POST   /clients                - Создать клиента
POST   /clients/:id/topup      - Пополнить баланс
```

**Зависимости:**
- PostgreSQL (Users, Roles, Clients)
- Redis (Session cache)
- JWT library

### 2. Shipment Service (Port 8002)

**Ответственность:**
- Управление продуктами (отправлениями)
- Контроль жизненного цикла отправлений
- Управление маршрутами доставки
- Расчет тарифов

**Жизненный цикл отправления (14 статусов):**
```
DRAFT → CREATED → PAYMENT_PENDING → PAID → READY_FOR_LOADING
→ LOADED → IN_TRANSIT → ARRIVED → READY_FOR_ISSUE
→ ISSUED → CLOSED

Варианты сбоев:
- CANCELLED (отмена)
- ON_HOLD (удержание)
- DAMAGED (повреждение)
```

**Ключевые методы:**
- `Create()` - Создание отправления
- `CalculateTariff()` - Расчет цены
- `SendToPayment()` - Отправка на оплату
- `Dispatch()` - Отправка груза
- `MarkTransit()` - Отметить в пути
- `Arrive()` - Груз прибыл
- `Issue()` - Выдать груз получателю
- `Close()` - Закрыть отправление

**API:**
```
POST   /shipments                    - Создать
GET    /shipments/:id                - Получить
GET    /shipments                    - Список
PUT    /shipments/:id                - Обновить
POST   /shipments/:id/calculate-tariff - Расчет
POST   /shipments/:id/send-to-payment  - На оплату
POST   /shipments/:id/dispatch       - Отправить
POST   /shipments/:id/arrive         - Прибыл
POST   /shipments/:id/issue          - Выдать
POST   /shipments/:id/close          - Закрыть
POST   /shipments/:id/cancel         - Отменить
POST   /shipments/:id/damage         - Повредить
```

### 3. Payment Service (Port 8003)

**Ответственность:**
- Обработка платежей
- Подтверждение платежей
- Синхронизация статуса оплаты с отправлением

**API:**
```
POST   /payments                - Создать платеж
GET    /payments/:id            - Получить платеж
POST   /payments/:id/confirm    - Подтвердить платеж
```

**Взаимодействие:**
- Получает информацию о отправлении из Shipment Service
- Обновляет статус отправления после подтверждения
- Создает записи в Audit Service

### 4. Tracking Service (Port 8004)

**Ответственность:**
- Генерация QR кодов
- Регистрация сканирований на станциях
- Отслеживание истории доставки

**API:**
```
POST   /tracking/qrcode         - Генерировать QR код
GET    /tracking/:code          - Получить информацию по коду
POST   /tracking/scan           - Зарегистрировать сканирование
GET    /tracking/:id/events     - История сканирований
GET    /tracking/:id/history    - Полная история
```

**Взаимодействие:**
- Получает данные отправлений из Shipment Service
- Создает события сканирования
- Уведомляет Notification Service

### 5. Notification Service (Port 8005)

**Ответственность:**
- Управление уведомлениями пользователям
- Уведомления о статусе отправлений
- Маркиров уведомлений как прочитанные

**API:**
```
GET    /notifications           - Получить уведомления
PUT    /notifications/:id/read  - Отметить как прочитанное
```

### 6. Reference Service (Port 8006)

**Ответственность:**
- Управление справочными данными
- Список ролей в системе
- Управление станциями доставки

**API:**
```
GET    /roles                   - Список ролей
GET    /stations                - Список станций
POST   /stations                - Создать станцию
PUT    /stations/:id            - Обновить станцию
```

### 7. Audit Service (Port 8007)

**Ответственность:**
- Логирование всех действий пользователей
- Отслеживание изменений в системе
- Историческая запись операций

**API:**
```
GET    /audit                   - История действий
GET    /audit/filter            - Фильтруемая история
```

### 8. Report Service (Port 8008)

**Ответственность:**
- Формирование отчетов
- Аналитика и статистика
- Агрегация данных из других сервисов

**API:**
```
GET    /reports/dashboard       - Панель управления
GET    /reports/finance         - Финансовый отчет
GET    /reports/status-summary  - Сводка по статусам
```

## Межсервисное взаимодействие

### Синхронное (HTTP/REST)

Сервисы вызывают друг друга напрямую через HTTP:

```
Payment Service          Shipment Service
     │                        │
     └──────GET /shipments/:id──►
     │◄───────JSON response────┘
     │
     └──────PUT /shipments/:id──►
     │         (update status)
     │◄────────200 OK───────────┘
```

**Примеры вызовов:**
```go
// Payment Service получает информацию об отправлении
resp, err := http.Get("http://shipment-service:8002/shipments/" + shipmentID)

// Payment Service обновляет статус отправления
req, _ := http.NewRequest("PUT", "http://shipment-service:8002/shipments/"+shipmentID, body)
```

### Асинхронное (Events) - Планируется

Использование message queue для событий:

```
Shipment Service (Publisher)     Message Queue (Kafka/RabbitMQ)     Subscribing Services
   │                                  │                                    │
   ├── Emit: ShipmentCreated ────────►├── Topic: shipment.events ────────►├─ Notification Service
   │                                  │                                    ├─ Audit Service
   ├── Emit: ShipmentDispatched ─────►│                                    ├─ Report Service
   │                                  │
   └── Emit: ShipmentDelivered ──────►│
```

## Взаимодействие с внешними системами

### PostgreSQL Database

```
Services ──► PostgreSQL
   │         ├── users
   │         ├── shipments
   │         ├── payments
   │         ├── scan_events
   │         ├── notifications
   │         ├── audit_logs
   │         └── ...
```

### Redis Cache

```
Services ──► Redis
   │         ├── Session cache (Auth Service)
   │         ├── QR Code cache (Tracking Service)
   │         ├── Rate limiting
   │         └── Temporary data
```

## Безопасность

### Аутентификация

1. Пользователь отправляет credentials на Auth Service
2. Auth Service выпускает JWT токен
3. Токен валидируется на каждого запроса через middleware

```go
// Middleware проверяет JWT токен
func AuthMiddleware(token string) (*Claims, error) {
    // Парсинг и валидация токена
    // Проверка подписи
    // Проверка срока действия
}
```

### Авторизация

```go
// Role-based access control
func RoleMiddleware(requiredRole string) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        user := GetAuthUser(r.Context())
        if user.Role != requiredRole {
            http.Error(w, "Forbidden", http.StatusForbidden)
            return
        }
    }
}
```

### CORS

```go
// Разрешение кроссдоменных запросов
func CORSMiddleware(w http.ResponseWriter) {
    w.Header().Set("Access-Control-Allow-Origin", "*")
    w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
    w.Header().Set("Access-Control-Allow-Headers", "Authorization, Content-Type")
}
```

## Масштабирование

### Горизонтальное масштабирование

Каждый микросервис может быть масштабирован независимо:

```yaml
services:
  auth-service:
    replicas: 3          # 3 экземпляра Auth Service
    
  shipment-service:
    replicas: 5          # 5 экземпляров Shipment Service
    
  payment-service:
    replicas: 2          # 2 экземпляра Payment Service
```

### Load Balancing

```
Load Balancer (Nginx)
     │
     ├──► Auth Service #1:8001
     ├──► Auth Service #2:8001
     ├──► Auth Service #3:8001
     │
     ├──► Shipment Service #1:8002
     ├──► Shipment Service #2:8002
     └──► Shipment Service #3:8002
```

### Кэширование

```go
// Redis для кэширования часто запрашиваемых данных
cache.Set("shipment:" + id, shipment, 5*time.Minute)
shipment, _ := cache.Get("shipment:" + id)
```

## Мониторинг и наблюдаемость

### Логирование

```go
// Структурированные логи
log.WithFields(logrus.Fields{
    "service": "auth-service",
    "action": "login",
    "user_id": userID,
    "status": "success",
}).Info("User logged in")
```

### Метрики (Prometheus)

```go
// Сбор метрик
requestDuration.Observe(duration.Seconds())
requestCount.WithLabelValues("POST", "/v1/shipments", "200").Inc()
```

### Трассировка (Jaeger)

```go
// Распределенная трассировка
span, ctx := opentracing.StartSpanFromContext(ctx, "CreateShipment")
defer span.Finish()
```

## Развертывание

### Docker

```bash
# Построить образ
docker build -t cargotrans/auth-service:v1.0 ./auth-service

# Запустить контейнер
docker run -p 8001:8001 cargotrans/auth-service:v1.0
```

### Docker Compose (Development)

```bash
docker-compose up -d
```

### Kubernetes (Production)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
      - name: auth-service
        image: cargotrans/auth-service:v1.0
        ports:
        - containerPort: 8001
        env:
        - name: DB_HOST
          value: postgres-service
```

## Управление ошибками

### Структурированные ошибки

```go
type AppError struct {
    Code    string
    Message string
    Details map[string]interface{}
}

// Использование
return &AppError{
    Code: "INVALID_SHIPMENT_STATUS",
    Message: "Cannot transition from current status",
    Details: map[string]interface{}{
        "current_status": "DRAFT",
        "requested_action": "dispatch",
    },
}
```

### HTTP Error Responses

```go
// 400 Bad Request
{
    "error": "INVALID_REQUEST",
    "message": "Invalid shipment data",
    "details": {...}
}

// 401 Unauthorized
{
    "error": "UNAUTHORIZED",
    "message": "Invalid or missing authorization token"
}

// 403 Forbidden
{
    "error": "FORBIDDEN",
    "message": "User does not have permission to perform this action"
}

// 500 Internal Server Error
{
    "error": "INTERNAL_ERROR",
    "message": "An unexpected error occurred"
}
```

## Версионирование API

```
/v1/shipments      - Version 1 API
/v2/shipments      - Version 2 API
/v3/shipments      - Version 3 API
```

## Графи зависимостей сервисов

```
┌──────────────┐
│ Auth Service │ (базовая аутентификация)
└──────┬───────┘
       │
       ├────────────────────────────────────────┐
       │                                        │
       ▼                                        ▼
┌──────────────────┐                  ┌──────────────────┐
│ Shipment Service │ (основной)       │ Reference Svc    │
└────────┬──────────┘ (отправления)   └──────┬───────────┘
         │                                  │
         ├─────────────┬────────────────────┼─────────┐
         │             │                    │         │
         ▼             ▼                    │         ▼
    ┌──────────┐  ┌────────────┐           │    ┌──────────┐
    │ Payment  │  │  Tracking  │           │    │ Audit    │
    │ Service  │  │  Service   │           │    │ Service  │
    └──────────┘  └──────┬─────┘           │    └──────────┘
         │                │                │         ▲
         │                ▼                │         │
         │         ┌──────────────┐        │         │
         │         │Notification  │        │         │
         │         │Service       │        │         │
         │         └──────────────┘        │         │
         │                                 │         │
         └─────────────────┬────────────────┘         │
                           │                          │
                           ▼                          │
                    ┌──────────────┐                  │
                    │ Report       │──────────────────┘
                    │ Service      │
                    └──────────────┘
```

## Выводы

Microservices архитектура CargoTrans обеспечивает:

✅ **Масштабируемость** - каждый сервис масштабируется независимо
✅ **Гибкость** - сервисы могут быть развер и обновлены отдельно
✅ **Надежность** - отказ одного сервиса не влияет на другие
✅ **Разработка** - разные команды работают на разных сервисах
✅ **Тестируемость** - сервисы могут тестироваться независимо
✅ **Технологическое многообразие** - сервисы могут использовать разные технологии

---

**Документ:** Architecture Design Document v1.0
**Последнее обновление:** 2024
**Статус:** Production Ready
