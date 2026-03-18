# Audit Service

Микросервис логирования и аудита действий пользователей.

## Функционал

- Получение логов аудита
- Фильтрация по типу сущности и действию
- Просмотр истории изменений

## API Endpoints

- `GET /audit` - Список логов аудита
- `GET /audit/filter` - Фильтрация логов (по типу сущности, действию, пользователю)

## Структура

```
audit-service/
├── adapters/
│   ├── operator/
│   │   └── handle/
│   └── service/
│       └── database/
├── core/
│   ├── domain/
│   │   ├── models/
│   │   └── data/
│   ├── ports/
│   └── services/
├── go.mod
└── README.md
```

## Типы сущностей

- SHIPMENT
- PAYMENT
- USER
- EMPLOYEE
- CLIENT
- STATION

## Действия

- CREATE - Создание
- UPDATE - Обновление
- DELETE - Удаление
- STATUS_CHANGE - Изменение статуса
- CONFIRM - Подтверждение
