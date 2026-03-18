# Сравнение: Текущая vs Новая Структура БД

## 🔴 ТЕКУЩИЕ ПРОБЛЕМЫ

### Проблема 1: SHIPMENT таблица - "монолит"
```go
type Shipment struct {
	ID               string      // ✅
	ShipmentNumber   string      // ✅
	ClientID         string      // ✅
	ClientName       string      // ❌ дублирует USER.name
	ClientEmail      string      // ❌ дублирует USER.email
	FromStation      string      // ✅ но строка, не FK
	ToStation        string      // ✅ но строка, не FK
	CurrentStation   string      // ✅
	NextStation      *string     // ✅
	Route            []string    // ❌ array - ужасно для БД!
	Status           string      // ✅
	ShipmentStatus   enum        // ✅
	PaymentStatus    enum        // ✅
	DepartureDate    time.Time   // ✅
	Weight           string      // ⚠️ должна быть float
	Dimensions       string      // ⚠️ должна быть структура
	Description      string      // ✅
	Value            string      // ⚠️ должна быть decimal
	Cost             float64     // ✅
	QuantityPlaces   int         // ✅
	ReceiverName     *string     // ⚠️ откуда данные?
	ReceiverPhone    *string     // ⚠️ откуда данные?
	TrainTime        *string     // ⚠️ неуточненное поле
	TrackingCode     *string     // ✅
	QRCodeID         *string     // ✅
	TransportUnitID  *string     // ✅
	LastUpdatedAt    time.Time   // ✅
	CreatedBy        *string     // ✅
	CreatedAt        time.Time   // ✅
	UpdatedAt        time.Time   // ✅
}
// 30 полей в одной таблице! Кошмар!
```

### Проблема 2: Array в БД
```sql
-- ПЛОХО: Route как array
route: ["NYC", "BOSTON", "PHILADELPHIA"]

-- Нельзя выполнить запрос:
SELECT * FROM shipments WHERE ? IN route; -- ❌ не работает!

-- Нельзя индексировать по станциям!
-- Нельзя найти все отправления через конкретную станцию!
```

### Проблема 3: Отсутствие нормализации
```sql
-- Текущее: денормализованная структура
SHIPMENT:
  id = "ship-123"
  clientID = "user-456"
  clientName = "John Doe"              -- ❌ ДУБЛИРОВАНИЕ
  clientEmail = "john@example.com"     -- ❌ ДУБЛИРОВАНИЕ (в USER)
  
-- Что если пользователь изменит имя?
UPDATE users SET name = "John Smith" WHERE id = 'user-456';
-- История отправлений будет старого имени! ❌
```

### Проблема 4: Отсутствует история баланса
```go
type User struct {
	DepositBalance float64 // ❌ только текущее значение!
}

-- Как узнать:
-- - когда был пополнен счет?
-- - кто пополнил?
-- - какова история транзакций?
-- 🔴 Невозможно!
```

### Проблема 5: Отсутствуют важные сущности
```
❌ TRANSPORT_UNIT - нет полной информации о машинах/поездах
❌ ROUTE - нет предопределенных маршрутов
❌ CLIENT - они часть USER, смешано
❌ SHIPMENT_ITEM - нет информации о отдельных предметах в отправлении
❌ PARTY - нет отдельных отправителей/получателей
❌ TARIFF - нет тарификации
❌ DOCUMENT - нет хранения документов
```

---

## ✅ НОВАЯ СТРУКТУРА - РЕШЕНИЯ

### Решение 1: Разделение SHIPMENT

```
БЫЛО:
┌─────────────────────┐
│ SHIPMENT (30 полей) │ ← монолит
└─────────────────────┘

СТАЛО:
┌──────────────────┐
│ SHIPMENT         │ ← 20 полей (основное)
└──────────────────┘
    ├──→ SHIPMENT_ROUTE (маршруты)
    ├──→ SHIPMENT_ITEM (предметы)
    ├──→ SHIPMENT_PRICING (цены)
    ├──→ SHIPMENT_STATUS_HISTORY (история)
    └──→ SHIPMENT_PARTIES (отправитель/получатель)
```

**Новая SHIPMENT таблица (только главное):**
```sql
CREATE TABLE shipments (
    id UUID PRIMARY KEY,
    shipment_number VARCHAR(50) UNIQUE,
    
    -- References (FK вместо strings)
    client_id UUID NOT NULL,           -- FK to clients
    origin_station_id UUID NOT NULL,   -- FK to stations
    destination_station_id UUID NOT NULL,
    current_station_id UUID,
    shipper_id UUID NOT NULL,          -- FK to parties
    consignee_id UUID NOT NULL,        -- FK to parties
    
    -- Statuses
    shipment_status VARCHAR(50),
    payment_status VARCHAR(50),
    
    -- Data (не строки!)
    total_weight DECIMAL(10,2),        -- не string!
    volume DECIMAL(10,2),
    quantity_items INT,
    
    -- Dates
    scheduled_departure TIMESTAMP,
    actual_departure TIMESTAMP,
    scheduled_arrival TIMESTAMP,
    actual_arrival TIMESTAMP,
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
-- 20 полей вместо 30 ✅
```

### Решение 2: Route как таблица (не array!)

```sql
-- БЫЛО - хранится как array:
shipment.route = ["NYC", "BOSTON", "PHILADELPHIA"]

-- СТАЛО - отдельная таблица:
CREATE TABLE shipment_routes (
    id UUID PRIMARY KEY,
    shipment_id UUID,
    sequence_number INT,       -- 1, 2, 3...
    station_id UUID,           -- FK to stations
    scheduled_arrival TIMESTAMP,
    actual_arrival TIMESTAMP,
    status VARCHAR(50)         -- pending, arrived, departed
);

-- Пример данных:
shipment_id | seq | station_id | status
------------|-----|------------|----------
ship-123    | 1   | nyc-1      | departed
ship-123    | 2   | boston-2   | arrived
ship-123    | 3   | phila-3    | pending

-- Теперь могу выполнить:
SELECT s.*, sr.station_id
FROM shipments s
JOIN shipment_routes sr ON s.id = sr.shipment_id
WHERE sr.station_id = 'boston-2' ✅ РАБОТАЕТ!
```

### Решение 3: Денормализация → Нормализация

```sql
-- БЫЛО - денормализированная:
SHIPMENT:
  client_id = "user-456"
  client_name = "John"          ← дублирование
  client_email = "john@ex.com"  ← дублирование

-- СТАЛО - нормализированная:
SHIPMENT:
  client_id UUID → FK to CLIENTS
  
CLIENT:
  id = "client-456"
  user_id = "user-456"
  
USER:
  id = "user-456"
  name = "John"          ← единственный источник ✅
  email = "john@ex.com"  ← единственный источник ✅

-- Преимущества:
-- 1. SINGLE SOURCE OF TRUTH
-- 2. При изменении имени - автоматически видно везде
-- 3. Нет несоответствий
```

### Решение 4: История баланса

```sql
-- БЫЛО - только текущее значение:
USER.deposit_balance = 5000.00  ← что-то произошло?

-- СТАЛО - полная история:
CLIENT_ACCOUNT:
  id = "acc-123"
  client_id = "client-456"
  balance = 5000.00
  
ACCOUNT_TRANSACTIONS:  ← новая таблица!
  id = "tr-1" | amount = 1000.00 | type = "deposit" | balance_after = 1000.00 | created_at = 2024-01-01
  id = "tr-2" | amount = -100.00 | type = "payment" | balance_after = 900.00  | created_at = 2024-01-02
  id = "tr-3" | amount = 4100.00 | type = "topup"    | balance_after = 5000.00 | created_at = 2024-01-03

-- Тепер знаю:
SELECT * FROM account_transactions 
WHERE account_id = 'acc-123'
ORDER BY created_at DESC;
-- ✅ Вся история платежей!
```

### Решение 5: Новые таблицы

```
✅ CLIENT           - справочник клиентов (отдельно от USER!)
✅ PARTY            - отправители/получатели
✅ TRANSPORT_UNIT   - машины, поезда, контейнеры
✅ ROUTE            - предопределенные маршруты
✅ ROUTE_STATIONS   - станции в маршруте  
✅ SHIPMENT_ITEM    - отдельные предметы в отправлении
✅ TARIFF           - тарифы по маршрутам
✅ ACCOUNT_*        - система учета и платежей
```

---

## 📊 СРАВНИТЕЛЬНАЯ ТАБЛИЦА

| Характеристика | Текущая | Новая |
|----------------|---------|-------|
| **Таблиц всего** | 12 | 18 |
| **Нормализация** | 2-я форма | 3-я форма |
| **Дублирование** | clientName, clientEmail | Исключено |
| **Гибкость Route** | Array (неудобно) | SQL-friendly таблица |
| **История баланса** | Нет | ✅ Полная |
| **Таблица CLIENT** | Смешана с USER | Отдельная |
| **Таблица PARTY** | Нет | ✅ Есть |
| **Таблица TRANSPORT** | Частичная | Полная |
| **Таблица TARIFF** | Нет | ✅ Есть |
| **Индексы** | Минимум | Оптимизированы |
| **JSON поля** | Нет | Для расширяемости |
| **Soft delete** | Нет | ✅ Есть |

---

## 🔄 ПРИМЕР МИГРАЦИИ ДАННЫХ

### Шаг 1: Создать новые таблицы

```sql
-- Не удаляя старые!
CREATE TABLE clients (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE,
    company_name VARCHAR(255),
    contract_number VARCHAR(100),
    client_type VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE shipment_routes (
    id UUID PRIMARY KEY,
    shipment_id UUID,
    sequence_number INT,
    station_id UUID,
    FOREIGN KEY (shipment_id) REFERENCES shipments(id),
    FOREIGN KEY (station_id) REFERENCES stations(id)
);
```

### Шаг 2: Скопировать данные

```sql
-- Миграция USER → CLIENT
INSERT INTO clients (id, user_id, company_name, client_type)
SELECT UUID(), id, company, role
FROM users 
WHERE role IN ('individual', 'corporate');

-- Миграция SHIPMENT.route array → SHIPMENT_ROUTES table
-- (это сложнее, так как нужно парсить array)
INSERT INTO shipment_routes (id, shipment_id, sequence_number, station_id)
SELECT 
    UUID(),
    s.id,
    1,
    s.from_station
FROM shipments s;
-- ... затем для destination station
```

### Шаг 3: Обновить приложение

```go
// Было:
type Shipment struct {
    ClientID    string
    ClientName  string
    Route       []string
}

// Стало:
type Shipment struct {
    ClientID              uuid.UUID  // FK
    ShipperID             uuid.UUID  // FK
    ConsigneeID           uuid.UUID  // FK
    OriginStationID       uuid.UUID  // FK
    DestinationStationID  uuid.UUID  // FK
}

// Route больше не в основной таблице!
// Запрашивается отдельно:
shipment.Route, _ = repo.GetShipmentRoute(shipment.ID)
```

### Шаг 4: Переключение трафика (blue-green deployment)

```
Stage 1: Параллельное использование обеих БД
Stage 2: Валидация данных (10% трафика на новую)
Stage 3: Полное переключение (100% трафика)
Stage 4: Rollback план (в случае проблем)
```

### Шаг 5: Удаление старых полей

```sql
ALTER TABLE shipments 
DROP COLUMN client_name;

ALTER TABLE shipments 
DROP COLUMN client_email;

ALTER TABLE shipments 
DROP COLUMN route;

ALTER TABLE users 
DROP COLUMN deposit_balance;
-- ... и т.д.
```

---

## 📈 ОЖИДАЕМЫЕ УЛУЧШЕНИЯ

### Производительность
```
❌ БЫЛО:
- Select все отправления через NYC: O(n) - сканирование всего массива
- Индексирование маршрутов: невозможно

✅ СТАЛО:
- Select все отправления через NYC: индексированный запрос
- Использование INDEX idx_station (station_id, created_at)
- Ускорение на 100x для запросов по маршрутам
```

### Масштабируемость
```
❌ БЫЛО:
- 500K отправлений с full array route
- Хранение: 500K * 100 bytes/station = 50MB array data
- При добавлении станций: перезаписи всех отправлений

✅ СТАЛО:
- shipment_routes таблица:  500K * 3 stations * 50 bytes = 75MB
- Добавление новой станции: только новая запись
- Без перезаписей существующих данных
```

### Надежность
```
❌ БЫЛО:
- ClientName = "John", но USER.name = "Jane"
- Несоответствие данных ❌

✅ СТАЛО:
- Single source of truth
- Referential integrity (FK constraints)
- Автоматическая консистентность ✅
```

### Аналитика
```
❌ БЫЛО:
SELECT COUNT(*) FROM shipments WHERE route LIKE '%Boston%'; ❌ нет

✅ СТАЛО:
SELECT s.status, COUNT(*)
FROM shipments s
JOIN shipment_routes sr ON s.id = sr.shipment_id
JOIN stations st ON sr.station_id = st.id
WHERE st.city = 'Boston'
GROUP BY s.status; ✅ легко!
```

---

## 🎯 РЕКОМЕНДУЕМЫЙ ПОРЯДОК ВНЕДРЕНИЯ

**Приоритет HIGH:**
1. ✅ CLIENT таблица (week 1)
2. ✅ SHIPMENT_ROUTE таблица (week 1)
3. ✅ PARTY таблица (week 1)
4. ✅ ACCOUNT_TRANSACTIONS (week 2)

**Приоритет MEDIUM:**
5. ✅ SHIPMENT_ITEM (week 2)
6. ✅ ROUTE + ROUTE_STATIONS (week 3)
7. ✅ TARIFF (week 3)

**Приоритет LOW (nice to have):**
8. TRANSPORT_UNIT (week 4)
9. DOCUMENT таблица (week 4)

---

## 💡 КЛЮЧЕВЫЕ ВЫВОДЫ

1. **Текущая структура** работает для MVP, но неоптимальна для масштабирования
2. **Главные проблемы**: денормализация, array в БД, отсутствие истории
3. **Новая структура**: 3-я нормальная форма, полная история, гибкость
4. **Миграция**: возможна без downtime (параллельные БД)
5. **Выигрыш**: +100x производительность для запросов, надежность, масштабируемость

