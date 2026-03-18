# Shipment Service

Микросервис управления отправлениями и их жизненным циклом.

## Функционал

- Создание и редактирование отправлений
- Управление жизненным циклом отправлений (14 статусов)
- Расчет тарифов на доставку
- Отправка на оплату
- Погрузка и отправка грузов
- Отслеживание статуса в пути
- Приход и выдача отправлений
- Закрытие и отмена отправлений
- Управление претензиями (повреждение, удержание)

## Статусы отправления

1. DRAFT - Черновик
2. CREATED - Создан
3. PAYMENT_PENDING - Ожидание оплаты
4. PAID - Оплачен
5. READY_FOR_LOADING - Готов к погрузке
6. LOADED - Погружен
7. IN_TRANSIT - В пути
8. ARRIVED - Прибыл
9. READY_FOR_ISSUE - Готов к выдаче
10. ISSUED - Выдан
11. CLOSED - Закрыт
12. CANCELLED - Отменен
13. ON_HOLD - На удержании
14. DAMAGED - Поврежден

## API Endpoints

- `POST /shipments` - Создание отправления
- `GET /shipments/:id` - Получение отправления
- `GET /shipments` - Список отправлений
- `PUT /shipments/:id` - Редактирование отправления
- `POST /shipments/:id/calculate-tariff` - Расчет тарифа
- `POST /shipments/:id/send-to-payment` - Отправка на оплату
- `POST /shipments/:id/ready-for-loading` - Готов к погрузке
- `POST /shipments/:id/load` - Погрузка
- `POST /shipments/:id/dispatch` - Отправка
- `POST /shipments/:id/mark-transit` - Отметить в пути
- `POST /shipments/:id/arrive` - Прибыл
- `POST /shipments/:id/ready-for-issue` - Готов к выдаче
- `POST /shipments/:id/issue` - Выдать
- `POST /shipments/:id/close` - Закрыть
- `POST /shipments/:id/cancel` - Отменить
- `POST /shipments/:id/hold` - Удержать
- `POST /shipments/:id/damage` - Повредить

## Структура

```
shipment-service/
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
