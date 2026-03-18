# Рекомендации по Улучшению Базы Данных CargoGO

## Анализ Текущей Структуры

### ❌ Основные Проблемы

#### 1. **SHIPMENT таблица слишком большая (30 полей)**
**Проблема:**
- clientName, clientEmail - дублирование данных из USER
- Route хранится как array - сложно для запросов
- Смешивание разных типов данных в одной таблице

**Текущее:**
```
SHIPMENT: id, shipmentNumber, clientID, clientName, clientEmail, 
fromStation, toStation, currentStation, nextStation, route, 
status, shipmentStatus, paymentStatus, departureDate, weight, 
dimensions, description, value, cost, quantityPlaces, receiverName, 
receiverPhone, trainTime, trackingCode, qrCodeID, transportUnitID, 
lastUpdatedAt, createdBy, createdAt, updatedAt
```

#### 2. **Денормализация данных**
**Проблема:** clientName и clientEmail повторяют информацию из USER
**Почему плохо:** Если пользователь изменит имя/почту, история отправлений будет неправильной

#### 3. **Route как массив**
**Проблема:** `Route: ["NYC", "BOSTON", "PHILADELPHIA"]`
**Почему плохо:** 
- Нельзя выполнить SQL-запрос типа "найти все отправления через BOSTON"
- Сложно с индексацией
- Нарушение нормализации

#### 4. **Отсутствуют ключевые таблицы**
- TRANSPORT_UNIT (машины, поезда, отправления)
- ROUTE (предопределенные маршруты)
- CLIENT (отдельная таблица для клиентов)
- SHIPMENT_ITEM (детали груза)
- SHIPPER/CONSIGNEE (отправитель/получатель)
- TARIFF (тарифы и цены)
- DOCUMENTS (документы, счета)

#### 5. **DepositBalance в таблице USER**
**Проблема:** История рассчетов потеряется
**Почему плохо:**
- Нельзя проследить, когда был пополнен счет
- Нельзя отследить движение денежных средств
- Проблемы с отчетностью

---

## 🎯 РЕКОМЕНДУЕМАЯ НОВАЯ СТРУКТУРА

### Этап 1: Разделение SHIPMENT

Вместо одной большой таблицы создать несколько специализированных:

```
SHIPMENT (основная информация)
├── SHIPMENT_DETAIL (детали груза)
├── SHIPMENT_ROUTE (маршрут)
├── SHIPMENT_PARTICIPANTS (участники)
├── SHIPMENT_PRICING (тарифы)
└── SHIPMENT_STATUS_HISTORY (история статусов)
```

### Этап 2: Новые Справочные Таблицы

```
CLIENTS (справочник клиентов)
├── CLIENT_CONTACT (контакты клиента)
├── CLIENT_ADDRESS (адреса клиента)
└── CLIENT_BALANCE (баланс счета)

TRANSPORTS (транспортные средства)
├── TRANSPORT_CAPACITY (грузоподъемность)
└── TRANSPORT_SCHEDULE (расписание)

ROUTES (маршруты)
└── ROUTE_STATIONS (станции маршрута)

PRICING (тарификация)
├── TARIFF (тарифы)
└── TARIFF_RULES (правила)
```

---

## 📋 НОВАЯ ПОДРОБНАЯ СХЕМА БД

### 1. USER (без изменений, но с оптимизацией)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, -- FK to roles
    phone VARCHAR(20),
    company_id UUID, -- FK to companies
    primary_station_id UUID, -- FK to stations (default station)
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Удаленные поля:**
- ❌ company (строка) → ✅ company_id (FK)
- ❌ depositBalance → ✅ отдельная таблица CLIENT_ACCOUNT
- ❌ contractNumber → ✅ отдельная таблица CLIENT_CONTRACTS
- ❌ station (строка) → ✅ primary_station_id (FK)

---

### 2. CLIENT (новая таблица)

```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE, -- FK to users (при наличии akk)
    company_name VARCHAR(255) NOT NULL,
    contract_number VARCHAR(100) UNIQUE,
    contract_date DATE,
    registration_number VARCHAR(100),
    tax_id VARCHAR(100),
    client_type VARCHAR(50), -- 'individual', 'corporate'
    rating INT DEFAULT 5,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

### 3. CLIENT_ACCOUNT (новая таблица - для баланса)

```sql
CREATE TABLE client_accounts (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL UNIQUE,
    balance DECIMAL(15,2) DEFAULT 0,
    credit_limit DECIMAL(15,2),
    currency VARCHAR(3) DEFAULT 'USD',
    account_status VARCHAR(50) DEFAULT 'active', -- 'active', 'frozen', 'closed'
    last_transaction_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);
```

**Зачем отдельная таблица:**
- История изменений баланса в transaction_history
- Поддержка принципа кредитования
- Отдельное управление счетом

---

### 4. ACCOUNT_TRANSACTION (новая таблица)

```sql
CREATE TABLE account_transactions (
    id UUID PRIMARY KEY,
    account_id UUID NOT NULL,
    transaction_type VARCHAR(50), -- 'deposit', 'withdrawal', 'payment', 'refund'
    amount DECIMAL(15,2) NOT NULL,
    balance_before DECIMAL(15,2),
    balance_after DECIMAL(15,2),
    reference_type VARCHAR(50), -- 'shipment', 'payment', 'topup'
    reference_id UUID,
    description TEXT,
    created_by UUID, -- FK to users
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES client_accounts(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_account_date (account_id, created_at)
);
```

---

### 5. SHIPMENT (оптимизированная - только основная информация)

```sql
CREATE TABLE shipments (
    id UUID PRIMARY KEY,
    shipment_number VARCHAR(50) UNIQUE NOT NULL,
    client_id UUID NOT NULL, -- FK to clients
    
    -- Маршрут (FK вместо array)
    origin_station_id UUID NOT NULL, -- FK to stations
    destination_station_id UUID NOT NULL, -- FK to stations
    current_station_id UUID, -- FK to stations
    
    -- Участники
    shipper_id UUID NOT NULL, -- FK to parties
    consignee_id UUID NOT NULL, -- FK to parties
    
    -- Данные отправления
    shipment_status VARCHAR(50) NOT NULL DEFAULT 'DRAFT', -- enum
    payment_status VARCHAR(50) NOT NULL DEFAULT 'UNPAID', -- enum
    
    total_weight DECIMAL(10,2),
    volume DECIMAL(10,2),
    quantity_items INT,
    
    -- Цены
    base_cost DECIMAL(15,2),
    surcharges DECIMAL(15,2),
    total_cost DECIMAL(15,2),
    
    -- Даты
    scheduled_departure_date TIMESTAMP,
    scheduled_arrival_date TIMESTAMP,
    actual_departure_date TIMESTAMP,
    actual_arrival_date TIMESTAMP,
    
    -- Отслеживание
    tracking_code VARCHAR(100) UNIQUE,
    qr_code_id UUID, -- FK to qr_codes
    transport_unit_id UUID, -- FK to transport_units
    
    -- Управление
    created_by UUID NOT NULL, -- FK to users
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (client_id) REFERENCES clients(id),
    FOREIGN KEY (origin_station_id) REFERENCES stations(id),
    FOREIGN KEY (destination_station_id) REFERENCES stations(id),
    FOREIGN KEY (current_station_id) REFERENCES stations(id),
    FOREIGN KEY (shipper_id) REFERENCES parties(id),
    FOREIGN KEY (consignee_id) REFERENCES parties(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_client (client_id),
    INDEX idx_status (shipment_status),
    INDEX idx_tracking (tracking_code)
);
```

---

### 6. SHIPMENT_ROUTE (новая таблица - вместо array)

```sql
CREATE TABLE shipment_routes (
    id UUID PRIMARY KEY,
    shipment_id UUID NOT NULL,
    sequence_number INT NOT NULL,
    station_id UUID NOT NULL, -- FK to stations
    scheduled_arrival TIMESTAMP,
    actual_arrival TIMESTAMP,
    scheduled_departure TIMESTAMP,
    actual_departure TIMESTAMP,
    status VARCHAR(50), -- 'pending', 'arrived', 'departed', 'skipped'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shipment_id) REFERENCES shipments(id) ON DELETE CASCADE,
    FOREIGN KEY (station_id) REFERENCES stations(id),
    UNIQUE KEY unique_sequence (shipment_id, sequence_number),
    INDEX idx_station (station_id)
);
```

**Преимущества:**
```sql
-- Теперь можно такие запросы:
SELECT s.id, s.shipment_number 
FROM shipments s
JOIN shipment_routes sr ON s.id = sr.shipment_id
WHERE sr.station_id = 'BOSTON' AND sr.status = 'pending'
ORDER BY sr.sequence_number;
```

---

### 7. SHIPMENT_ITEM (новая таблица - детали груза)

```sql
CREATE TABLE shipment_items (
    id UUID PRIMARY KEY,
    shipment_id UUID NOT NULL,
    sequence_number INT NOT NULL,
    description VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    weight DECIMAL(10,2),
    volume DECIMAL(10,2),
    unit_price DECIMAL(15,2),
    declared_value DECIMAL(15,2),
    sku VARCHAR(100),
    commodity_code VARCHAR(50), -- HSCode
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shipment_id) REFERENCES shipments(id) ON DELETE CASCADE,
    UNIQUE KEY unique_item (shipment_id, sequence_number)
);
```

---

### 8. PARTY (новая таблица - отправитель/получатель)

```sql
CREATE TABLE parties (
    id UUID PRIMARY KEY,
    party_type VARCHAR(50) NOT NULL, -- 'shipper', 'consignee', 'contact'
    name VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    address_street VARCHAR(255),
    address_city VARCHAR(100),
    address_state VARCHAR(100),
    address_country VARCHAR(100),
    address_zip VARCHAR(20),
    tax_id VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_email (email)
);
```

---

### 9. TRANSPORT_UNIT (новая таблица)

```sql
CREATE TABLE transport_units (
    id UUID PRIMARY KEY,
    unit_number VARCHAR(50) UNIQUE NOT NULL,
    unit_type VARCHAR(50) NOT NULL, -- 'truck', 'train_car', 'container'
    status VARCHAR(50) DEFAULT 'available', -- 'available', 'in_transit', 'maintenance'
    capacity_weight DECIMAL(10,2),
    capacity_volume DECIMAL(10,2),
    current_load_weight DECIMAL(10,2),
    current_load_volume DECIMAL(10,2),
    current_location_station_id UUID, -- FK to stations
    last_maintenance_date DATE,
    driver_id UUID, -- FK to users
    current_shipment_id UUID, -- FK to shipments
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (current_location_station_id) REFERENCES stations(id),
    FOREIGN KEY (driver_id) REFERENCES users(id),
    FOREIGN KEY (current_shipment_id) REFERENCES shipments(id),
    INDEX idx_status (status),
    INDEX idx_location (current_location_station_id)
);
```

---

### 10. ROUTE (новая таблица - предопределенные маршруты)

```sql
CREATE TABLE routes (
    id UUID PRIMARY KEY,
    route_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    origin_city VARCHAR(100),
    destination_city VARCHAR(100),
    estimated_duration_hours INT,
    typical_cost DECIMAL(15,2),
    is_active BOOLEAN DEFAULT true,
    frequency VARCHAR(50), -- 'daily', 'twice_daily', 'weekly'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

```sql
CREATE TABLE route_stations (
    id UUID PRIMARY KEY,
    route_id UUID NOT NULL,
    sequence_number INT NOT NULL,
    station_id UUID NOT NULL,
    estimated_arrival_time INT, -- minutes from start
    typical_stop_duration INT, -- minutes
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE,
    FOREIGN KEY (station_id) REFERENCES stations(id),
    UNIQUE KEY unique_sequence (route_id, sequence_number)
);
```

---

### 11. TARIFF (новая таблица - тарифы)

```sql
CREATE TABLE tariffs (
    id UUID PRIMARY KEY,
    tariff_code VARCHAR(50) UNIQUE NOT NULL,
    tariff_name VARCHAR(255) NOT NULL,
    description TEXT,
    origin_station_id UUID NOT NULL,
    destination_station_id UUID NOT NULL,
    cargo_type VARCHAR(50), -- 'general', 'hazmat', 'fragile', 'perishable'
    weight_range_from DECIMAL(10,2),
    weight_range_to DECIMAL(10,2),
    price_per_unit DECIMAL(15,2),
    price_unit VARCHAR(50), -- 'kg', 'cbm', 'shipment'
    min_price DECIMAL(15,2),
    markup_percentage DECIMAL(5,2),
    is_active BOOLEAN DEFAULT true,
    valid_from DATE,
    valid_until DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (origin_station_id) REFERENCES stations(id),
    FOREIGN KEY (destination_station_id) REFERENCES stations(id),
    INDEX idx_route (origin_station_id, destination_station_id)
);
```

---

### 12. PAYMENT (оптимизированная)

```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY,
    shipment_id UUID NOT NULL,
    account_transaction_id UUID, -- FK to account_transactions
    amount DECIMAL(15,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL, -- 'cash', 'card', 'transfer', 'wallet'
    payment_status VARCHAR(50) NOT NULL, -- 'unpaid', 'pending', 'confirmed', 'failed', 'reversed'
    reference_code VARCHAR(100), -- POS reference, transaction ID
    paid_at TIMESTAMP,
    confirmed_by UUID, -- FK to users
    failed_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shipment_id) REFERENCES shipments(id),
    FOREIGN KEY (account_transaction_id) REFERENCES account_transactions(id),
    FOREIGN KEY (confirmed_by) REFERENCES users(id),
    INDEX idx_shipment (shipment_id),
    INDEX idx_status (payment_status)
);
```

---

### 13. QR_CODE (без изменений)

```sql
CREATE TABLE qr_codes (
    id UUID PRIMARY KEY,
    shipment_id UUID NOT NULL UNIQUE,
    qr_value VARCHAR(255) UNIQUE NOT NULL,
    png_data BYTEA, -- хранить изображение
    scans_count INT DEFAULT 0,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    FOREIGN KEY (shipment_id) REFERENCES shipments(id),
    INDEX idx_value (qr_value)
);
```

---

### 14. SCAN_EVENT (оптимизированная)

```sql
CREATE TABLE scan_events (
    id UUID PRIMARY KEY,
    shipment_id UUID NOT NULL,
    qr_code_id UUID, -- FK to qr_codes
    scan_type VARCHAR(50) NOT NULL, -- 'inbound', 'outbound', 'delivery', 'return'
    station_id UUID NOT NULL, -- FK to stations
    scanned_by_user_id UUID, -- FK to users
    transport_unit_id UUID, -- FK to transport_units
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    notes TEXT,
    gps_latitude DECIMAL(10,8),
    gps_longitude DECIMAL(11,8),
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shipment_id) REFERENCES shipments(id),
    FOREIGN KEY (qr_code_id) REFERENCES qr_codes(id),
    FOREIGN KEY (station_id) REFERENCES stations(id),
    FOREIGN KEY (scanned_by_user_id) REFERENCES users(id),
    FOREIGN KEY (transport_unit_id) REFERENCES transport_units(id),
    INDEX idx_shipment_date (shipment_id, scanned_at),
    INDEX idx_station_date (station_id, scanned_at),
    INDEX idx_qr_code (qr_code_id)
);
```

---

### 15. STATION (оптимизированная)

```sql
CREATE TABLE stations (
    id UUID PRIMARY KEY,
    station_code VARCHAR(50) UNIQUE NOT NULL,
    station_name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100),
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(255),
    manager_id UUID, -- FK to users
    opening_hours VARCHAR(255),
    storage_capacity DECIMAL(10,2),
    current_storage_used DECIMAL(10,2),
    is_active BOOLEAN DEFAULT true,
    is_distribution_center BOOLEAN DEFAULT false,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES users(id),
    INDEX idx_city (city),
    INDEX idx_code (station_code)
);
```

---

### 16. SHIPMENT_HISTORY (оптимизированная)

```sql
CREATE TABLE shipment_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    shipment_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    operator_id UUID, -- FK to users
    operator_name VARCHAR(255),
    station_id UUID, -- FK to stations
    details TEXT,
    reason VARCHAR(255),
    metadata JSON, -- для хранения доп. информации
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shipment_id) REFERENCES shipments(id) ON DELETE CASCADE,
    FOREIGN KEY (operator_id) REFERENCES users(id),
    FOREIGN KEY (station_id) REFERENCES stations(id),
    INDEX idx_shipment_date (shipment_id, created_at),
    INDEX idx_status_change (old_status, new_status)
);
```

---

### 17. NOTIFICATION (без изменений, но с индексами)

```sql
CREATE TABLE notifications (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id UUID NOT NULL,
    title VARCHAR(255),
    message TEXT NOT NULL,
    notification_type VARCHAR(50), -- 'email', 'sms', 'push', 'in-app'
    is_read BOOLEAN DEFAULT false,
    related_entity_type VARCHAR(50), -- 'shipment', 'payment', 'delivery'
    related_entity_id UUID,
    read_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_read (user_id, is_read),
    INDEX idx_user_date (user_id, created_at),
    INDEX idx_entity (related_entity_type, related_entity_id)
);
```

---

### 18. AUDIT_LOG (оптимизированная)

```sql
CREATE TABLE audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id UUID, -- FK to users
    entity_type VARCHAR(50) NOT NULL, -- 'shipment', 'payment', 'user', 'station'
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL, -- 'CREATE', 'UPDATE', 'DELETE', 'VIEW'
    old_values JSON, -- stores changed fields
    new_values JSON,
    ip_address VARCHAR(50),
    station_id UUID, -- FK to stations (where action happened)
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (station_id) REFERENCES stations(id),
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_user_date (user_id, created_at),
    INDEX idx_action (action),
    INDEX idx_date (created_at)
);
```

---

## 📊 НОВАЯ ЭРД-ДИАГРАММА

```
                    ┌─────────────┐
                    │    USER     │
                    └─────────────┘
                          ▼
          ┌───────────────────────────────┐
          ▼                               ▼
    ┌─────────────┐            ┌──────────────────┐
    │   CLIENT    │            │ ACCOUNT_TRANS    │
    └─────────────┘            └──────────────────┘
          ▼                               ▲
    ┌──────────────────┐          │      │
    │ CLIENT_ACCOUNT ◄─┴──────────┘      │
    └──────────────────┘                 │
                                         │
         ┌──────────────────────────────┘
         │
    ┌────────────────────────┐
    │    SHIPMENT (main)     │
    └────────────────────────┘
    /     │     │       │      \
   /      │     │       │       \
  ▼       ▼     ▼       ▼        ▼
ROUTE   ITEMS PRICE  PAYMENT  TRACKING
  │       │     │       │        │
  ▼       ▼     ▼       ▼        ▼
STATION PARTY TARIFF QR_CODE SCAN_EVENT
         │                      │
         ├──────────────────────┘
         │
    ┌────────────────────┐
    │ TRANSPORT_UNIT     │
    └────────────────────┘
```

---

## 🔄 МИГРАЦИОННЫЙ ПУТЬ

### Фаза 1: Создание новых таблиц (0 downtime)
1. Создать CLIENT таблицу
2. Создать PARTY таблицу
3. Создать SHIPMENT_ROUTE таблицу
4. Создать SHIPMENT_ITEM таблицу
5. Создать ACCOUNT_* таблицы

### Фаза 2: Миграция данных
```sql
-- Копирование данных из старой структуры
INSERT INTO clients (user_id, company_name, client_type)
SELECT id, company, role
FROM users WHERE role IN ('individual', 'corporate');

INSERT INTO shipment_routes (shipment_id, sequence_number, station_id)
SELECT s.id, ROW_NUMBER() OVER (PARTITION BY s.id), s.from_station
FROM shipments s;
```

### Фаза 3: Обновление приложения
1. Обновить Go модели
2. Обновить repository interfaces
3. Обновить queries

### Фаза 4: Переключение трафика
1. Параллельное использование обеих БД
2. Валидация данных
3. Полное переключение

### Фаза 5: Удаление старой структуры
```sql
ALTER TABLE shipments DROP COLUMN clientName;
ALTER TABLE shipments DROP COLUMN clientEmail;
ALTER TABLE shipments DROP COLUMN route;
ALTER TABLE users DROP COLUMN depositBalance;
ALTER TABLE users DROP COLUMN company;
ALTER TABLE users DROP COLUMN station;
```

---

## 📈 ПРЕИМУЩЕСТВА НОВОЙ СТРУКТУРЫ

| Аспект | Старая | Новая |
|--------|--------|-------|
| **Нормализация** | Денормализованная | 3-я нормальная форма |
| **Дублирование** | Много (clientName) | Минимум |
| **Гибкость** | Низкая | Высокая |
| **Запросы** | Route как array | SQL-friendly |
| **История баланса** | Нет | ✅ full audit |
| **Масштабируемость** | Проблемы с большими объемами | ✅ Готова |
| **报告** | Сложные | Простые SQL-запросы |
| **Производительность** | OK | ✅ Оптимизирована |

---

## 💾 SQL ИНДЕКСЫ ДЛЯ ОПТИМИЗАЦИИ

```sql
-- Critical indexes для производительности
CREATE INDEX idx_shipments_client ON shipments(client_id);
CREATE INDEX idx_shipments_status ON shipments(shipment_status);
CREATE INDEX idx_shipments_dates ON shipments(created_at, updated_at);
CREATE INDEX idx_scan_events_shipment ON scan_events(shipment_id, scanned_at);
CREATE INDEX idx_payments_status ON payments(payment_status);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_route_stations_seq ON route_stations(route_id, sequence_number);
```

---

## 🔒 SOFT DELETE

Добавить поле `deleted_at` для логического удаления:

```sql
ALTER TABLE shipments ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE payments ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE scan_events ADD COLUMN deleted_at TIMESTAMP NULL;

-- И всегда использовать в запросах:
SELECT * FROM shipments WHERE deleted_at IS NULL;
```

---

## 📝 ОСОБЕННОСТИ НОВОЙ СТРУКТУРЫ

1. ✅ **Разделение ответственности** - каждая таблица имеет четкое назначение
2. ✅ **Auditability** - все изменения отслеживаются
3. ✅ **Масштабируемость** - легко добавлять новые функции
4. ✅ **Производительность** - оптимальные индексы
5. ✅ **Гибкость** - JSON поля для расширяемости
6. ✅ **Compliance** - соответствует регуляторным требованиям

