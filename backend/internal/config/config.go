package config

import (
	"os"
	"strings"
)

type Config struct {
	Port        string
	DatabaseURL string
	JWTSecret   string

	LetsEncryptEnabled  bool
	LetsEncryptEmail    string
	LetsEncryptDomains  []string
	LetsEncryptCacheDir string
	LetsEncryptHTTPAddr string
	TLSAddr             string
}

func Load() Config {
	cfg := Config{
		Port:        getenv("PORT", "8080"),
		DatabaseURL: getenv("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/cargotrans?sslmode=disable"),
		JWTSecret:   getenv("JWT_SECRET", "dev-secret"),

		LetsEncryptEnabled:  getenvBool("LETSENCRYPT_ENABLED", false),
		LetsEncryptEmail:    getenv("LETSENCRYPT_EMAIL", ""),
		LetsEncryptDomains:  getenvCSV("LETSENCRYPT_DOMAINS"),
		LetsEncryptCacheDir: getenv("LETSENCRYPT_CACHE_DIR", "/tmp/autocert-cache"),
		LetsEncryptHTTPAddr: getenv("LETSENCRYPT_HTTP_ADDR", ":80"),
		TLSAddr:             getenv("TLS_ADDR", ":443"),
	}
	return cfg
}

func (c Config) Addr() string {
	return ":" + c.Port
}

func getenv(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func getenvBool(key string, fallback bool) bool {
	v := strings.ToLower(strings.TrimSpace(os.Getenv(key)))
	if v == "" {
		return fallback
	}
	switch v {
	case "1", "true", "yes", "y", "on":
		return true
	case "0", "false", "no", "n", "off":
		return false
	default:
		return fallback
	}
}

func getenvCSV(key string) []string {
	raw := strings.TrimSpace(os.Getenv(key))
	if raw == "" {
		return nil
	}
	parts := strings.Split(raw, ",")
	out := make([]string, 0, len(parts))
	for _, part := range parts {
		item := strings.TrimSpace(part)
		if item != "" {
			out = append(out, item)
		}
	}
	return out
}
