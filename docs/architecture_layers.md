# Layered architecture (Python services)

This repo follows a **strict 3-layer** style for `services/billing` and `services/inventory`:

## 1) Domain / core (`core/domain`, `core/exceptions`, `core/protocols`)

- **Entities, enums, value objects** — no I/O, no business rules.
- **Domain exceptions** — carry `error_code`, `message`, `context`, `http_status` (mapped at API boundary only).
- **Protocols (ports)** — interfaces implemented by SQLite adapters.

## 2) Application (`features/*/application`)

- **Use cases / services** — all business rules (state machines, tax math, validation).
- Depends only on **ports** and **Settings**, never on FastAPI.

## 3) API (`api/`)

- **Controllers** — parse/validate HTTP (Pydantic), enforce RBAC headers, call services.
- **Middleware** — `X-Request-Id`, `X-Tenant-Id` → logging contextvars.
- **Exception handlers** — `DomainException` → JSON; unexpected → generic 500.

## 4) Infrastructure (`infrastructure/`)

- **SQLite** — SQL and migrations; implements storage ports.

## API versioning

- **Preferred:** `/v1/...` on billing; `/v1/inventory/...` on inventory.
- **Legacy:** same routes without `/v1` remain mounted for backward compatibility.
- **Gateway** proxies both styles.

## Multi-tenancy

- Every persisted row is scoped by **`tenant_id`** (header `X-Tenant-Id`, default from env `DEFAULT_TENANT_ID`).

## Observability

- Shared library: `libs/observability` — install with `pip install ./libs/observability` (package name `restro-observability`).
- Structured **JSON logs** (toggle `LOG_JSON=false` for plain text locally).
- Logs include **request_id**, **tenant_id**, **service_name**, **method_name**, **status** where applicable.
