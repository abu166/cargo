package middleware

import (
	"context"
	"net/http"
	"strings"

	"cargo/backend/microservices/auth-service/core/domain/models"
	"cargo/backend/microservices/auth-service/core/services"
)

type contextKey string

const AuthContextKey contextKey = "auth_user"

// AuthMiddleware проверяет JWT токен в заголовке Authorization
func AuthMiddleware(authService services.AuthService) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Получить токен из заголовка
			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				http.Error(w, "Missing authorization header", http.StatusUnauthorized)
				return
			}

			// Извлечь токен из "Bearer <token>"
			parts := strings.Split(authHeader, " ")
			if len(parts) != 2 || parts[0] != "Bearer" {
				http.Error(w, "Invalid authorization header format", http.StatusUnauthorized)
				return
			}

			token := parts[1]

			// Проверить токен
			claims, err := authService.ParseToken(r.Context(), token)
			if err != nil {
				http.Error(w, "Invalid token", http.StatusUnauthorized)
				return
			}

			// Добавить пользователя в контекст
			user := services.AuthenticatedUser{
				ID:    claims.UserID,
				Email: claims.Email,
				Role:  claims.Role,
				Name:  claims.Name,
			}

			ctx := context.WithValue(r.Context(), AuthContextKey, user)
			r = r.WithContext(ctx)

			next.ServeHTTP(w, r)
		})
	}
}

// RoleMiddleware проверяет, имеет ли пользователь необходимую роль
func RoleMiddleware(requiredRoles ...models.Role) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			user, ok := r.Context().Value(AuthContextKey).(services.AuthenticatedUser)
			if !ok {
				http.Error(w, "Unauthorized", http.StatusUnauthorized)
				return
			}

			// Проверить роль
			hasRole := false
			for _, role := range requiredRoles {
				if user.Role == role {
					hasRole = true
					break
				}
			}

			if !hasRole {
				http.Error(w, "Forbidden", http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// GetAuthUser извлекает пользователя из контекста
func GetAuthUser(r *http.Request) (services.AuthenticatedUser, bool) {
	user, ok := r.Context().Value(AuthContextKey).(services.AuthenticatedUser)
	return user, ok
}
