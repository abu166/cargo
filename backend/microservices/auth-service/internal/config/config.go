package config

import (
	"os"
	"strconv"
	"time"
)

type Config struct {
	Server   ServerConfig
	Database DatabaseConfig
	Redis    RedisConfig
	JWT      JWTConfig
}

type ServerConfig struct {
	Port         int
	Host         string
	ReadTimeout  time.Duration
	WriteTimeout time.Duration
}

type DatabaseConfig struct {
	Host     string
	Port     int
	User     string
	Password string
	DBName   string
	SSLMode  string
	MaxConn  int
}

type RedisConfig struct {
	Host     string
	Port     int
	Password string
	DB       int
}

type JWTConfig struct {
	Secret    string
	ExpiresIn time.Duration
}

func LoadConfig() *Config {
	cfg := &Config{
		Server: ServerConfig{
			Port:         getEnvInt("AUTH_SERVICE_PORT", 8001),
			Host:         getEnvString("AUTH_SERVICE_HOST", "0.0.0.0"),
			ReadTimeout:  15 * time.Second,
			WriteTimeout: 15 * time.Second,
		},
		Database: DatabaseConfig{
			Host:     getEnvString("DB_HOST", "localhost"),
			Port:     getEnvInt("DB_PORT", 5432),
			User:     getEnvString("DB_USER", "cargotrans"),
			Password: getEnvString("DB_PASSWORD", "cargotrans_password"),
			DBName:   getEnvString("DB_NAME", "cargotrans_db"),
			SSLMode:  getEnvString("DB_SSLMODE", "disable"),
			MaxConn:  getEnvInt("DB_MAX_CONN", 25),
		},
		Redis: RedisConfig{
			Host:     getEnvString("REDIS_HOST", "localhost"),
			Port:     getEnvInt("REDIS_PORT", 6379),
			Password: getEnvString("REDIS_PASSWORD", ""),
			DB:       0,
		},
		JWT: JWTConfig{
			Secret:    getEnvString("JWT_SECRET", "your_jwt_secret_key_here"),
			ExpiresIn: 24 * time.Hour,
		},
	}
	return cfg
}

func getEnvString(key, defaultValue string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value, exists := os.LookupEnv(key); exists {
		if intVal, err := strconv.Atoi(value); err == nil {
			return intVal
		}
	}
	return defaultValue
}
