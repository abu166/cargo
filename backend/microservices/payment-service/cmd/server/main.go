package main

import (
	"fmt"
	"log"
	"net/http"

	"cargo/backend/microservices/payment-service/internal/config"
	"cargo/backend/microservices/payment-service/internal/middleware"
)

func main() {
	// Загрузить конфигурацию
	cfg := config.LoadConfig()

	log.Printf("Starting Payment Service on %s:%d", cfg.Server.Host, cfg.Server.Port)

	// Инициализировать сервисы
	// TODO: Инициализировать database repository
	// paymentService := services.NewPaymentService(repo)

	// Создать HTTP сервер
	mux := http.NewServeMux()

	// Применить middleware
	var handler http.Handler = mux
	handler = middleware.CORSMiddleware(handler)
	handler = middleware.RecoveryMiddleware(handler)
	handler = middleware.LoggerMiddleware(handler)

	// Зарегистрировать обработчики
	// TODO: Добавить обработчики для маршрутов

	// Запустить сервер
	addr := fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port)
	server := &http.Server{
		Addr:         addr,
		Handler:      handler,
		ReadTimeout:  cfg.Server.ReadTimeout,
		WriteTimeout: cfg.Server.WriteTimeout,
	}

	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("Server error: %v", err)
	}
}
