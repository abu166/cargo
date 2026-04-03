# CargoTrans Backend

Go backend for CargoTrans, using PostgreSQL instead of SQLite while keeping the `/api/...` contract expected by the current frontend and adding the remaining pilot APIs.

## Structure

- `cmd/server`: application entrypoint
- `internal/api`: HTTP handlers split by domain
- `internal/service`: application/use-case layer split by domain
- `internal/storage/postgres`: PostgreSQL adapters and schema bootstrap
- `internal/model`: domain models
- `postman`: importable Postman collection and environment

## Run locally

With Docker:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8080` and PostgreSQL at `localhost:5432`.

Without Docker:

1. Start PostgreSQL.
2. Set env vars if needed:

```bash
export DATABASE_URL="postgres://postgres:postgres@localhost:5432/cargotrans?sslmode=disable"
export JWT_SECRET="dev-secret"
export PORT="8080"
```

3. Run the server:

```bash
go run ./cmd/server
```

## HTTPS with Let's Encrypt

Set these environment variables to enable automatic certificates:

```bash
export LETSENCRYPT_ENABLED="true"
export LETSENCRYPT_EMAIL="ops@example.com"
export LETSENCRYPT_DOMAINS="api.example.com"
export LETSENCRYPT_HTTP_ADDR=":80"
export TLS_ADDR=":443"
```

Notes:

- `LETSENCRYPT_DOMAINS` accepts comma-separated values.
- Port `80` must be reachable from the internet for ACME HTTP-01 challenge.
- Certificates are cached in `LETSENCRYPT_CACHE_DIR` (default `/tmp/autocert-cache`).

## Test

```bash
go test ./...
```

## Postman

Import:

- `postman/cargotrans.postman_collection.json`
- `postman/cargotrans.postman_environment.json`
