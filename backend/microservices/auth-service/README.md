# Auth Service

Микросервис управления аутентификацией и авторизацией.

## Функционал

- Регистрация и вход пользователей
- Управление JWT токенами
- Управление сотрудниками (создание, редактирование, удаление)
- Управление корпоративными клиентами
- Управление ролями и правами доступа

## API Endpoints

### Аутентификация
- `POST /auth/register` - Регистрация пользователя
- `POST /auth/login` - Вход пользователя
- `GET /auth/me` - Получение текущего пользователя

### Сотрудники
- `GET /admin/employees` - Список сотрудников
- `POST /admin/employees` - Создание сотрудника
- `PUT /admin/users/:id` - Обновление пользователя
- `DELETE /admin/employees/:id` - Удаление сотрудника

### Корпоративные клиенты
- `GET /clients` - Список корпоративных клиентов
- `POST /clients` - Создание корпоративного клиента
- `POST /clients/:id/topup` - Пополнение баланса

## Структура

```
auth-service/
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

## Зависимости

- github.com/golang-jwt/jwt/v5 - JWT токены
- github.com/google/uuid - UUID генератор
- golang.org/x/crypto - Криптография (bcrypt)
