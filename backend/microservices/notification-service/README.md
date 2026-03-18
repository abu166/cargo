# Notification Service

Микросервис управления уведомлениями пользователям.

## Функционал

- Получение уведомлений пользователя
- Отметить уведомление как прочитанное
- Фильтрация непрочитанных уведомлений

## API Endpoints

- `GET /notifications` - Список уведомлений текущего пользователя
- `PUT /notifications/:id/read` - Отметить как прочитанное

## Структура

```
notification-service/
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

## Интеграция

Этот микросервис взаимодействует с:
- Auth Service - для аутентификации пользователей
- Shipment Service - для создания уведомлений о статусе
