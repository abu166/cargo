# Reference Service

Микросервис управления справочными данными (станции, роли).

## Функционал

- Получение списка ролей
- Получение списка станций
- Создание новой станции
- Обновление информации о станции

## API Endpoints

- `GET /roles` - Список ролей
- `GET /stations` - Список станций
- `POST /stations` - Создание станции
- `PUT /stations/:id` - Обновление станции

## Структура

```
reference-service/
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

## Роли

- admin - Администратор
- operator - Оператор
- client - Клиент
- employee - Сотрудник
- manager - Менеджер
