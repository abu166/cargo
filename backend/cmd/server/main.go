package main

import (
	"crypto/tls"
	"fmt"
	"log"
	"net"
	"net/http"

	"cargo/backend/internal/api"
	"cargo/backend/internal/config"
	"cargo/backend/internal/service"
	"cargo/backend/internal/storage/postgres"

	"golang.org/x/crypto/acme/autocert"
)

func main() {
	cfg := config.Load()

	db, err := postgres.Open(cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("open postgres: %v", err)
	}
	defer db.Close()

	// if err := db.Migrate(); err != nil {
	// 	log.Fatalf("migrate postgres: %v", err)
	// }

	repo := postgres.NewRepository(db.Pool())
	services := service.NewServices(repo, cfg.JWTSecret)
	server, err := api.NewServer(cfg, services)
	if err != nil {
		log.Fatalf("create server: %v", err)
	}

	if cfg.LetsEncryptEnabled {
		if len(cfg.LetsEncryptDomains) == 0 {
			log.Fatal("letsencrypt is enabled but LETSENCRYPT_DOMAINS is empty")
		}
		manager := &autocert.Manager{
			Prompt:     autocert.AcceptTOS,
			Email:      cfg.LetsEncryptEmail,
			Cache:      autocert.DirCache(cfg.LetsEncryptCacheDir),
			HostPolicy: autocert.HostWhitelist(cfg.LetsEncryptDomains...),
		}

		redirectToTLS := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			http.Redirect(w, r, buildHTTPSURL(r, cfg.TLSAddr), http.StatusMovedPermanently)
		})
		httpServer := &http.Server{
			Addr:    cfg.LetsEncryptHTTPAddr,
			Handler: manager.HTTPHandler(redirectToTLS),
		}
		go func() {
			log.Printf("http challenge server listening on %s", cfg.LetsEncryptHTTPAddr)
			if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
				log.Fatalf("http challenge server: %v", err)
			}
		}()

		httpsServer := &http.Server{
			Addr:    cfg.TLSAddr,
			Handler: server.Router(),
			TLSConfig: &tls.Config{
				GetCertificate: manager.GetCertificate,
				MinVersion:     tls.VersionTLS12,
			},
		}

		log.Printf("https server listening on %s with letsencrypt domains=%v", cfg.TLSAddr, cfg.LetsEncryptDomains)
		if err := httpsServer.ListenAndServeTLS("", ""); err != nil {
			log.Fatalf("listen tls: %v", err)
		}
		return
	}

	log.Printf("server listening on %s", cfg.Addr())
	if err := http.ListenAndServe(cfg.Addr(), server.Router()); err != nil {
		log.Fatalf("listen: %v", err)
	}
}

func buildHTTPSURL(r *http.Request, tlsAddr string) string {
	host := r.Host
	if parsedHost, _, err := net.SplitHostPort(r.Host); err == nil {
		host = parsedHost
	}
	_, tlsPort, err := net.SplitHostPort(tlsAddr)
	if err == nil && tlsPort != "443" {
		host = net.JoinHostPort(host, tlsPort)
	}
	if err != nil && tlsAddr != ":443" {
		host = fmt.Sprintf("%s:%s", host, tlsAddr)
	}
	return "https://" + host + r.URL.RequestURI()
}
