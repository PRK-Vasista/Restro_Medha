# Restro Medha MVP Monorepo

This repository implements the 16-week resilience-first MVP plan with:

- `apps/pos`: Next.js POS + manager dashboard
- `apps/handheld`: React Native app for waiter/kitchen
- `services/gateway`: Golang API gateway
- `services/billing`: FastAPI billing + GST + append-only ledger
- `services/inventory`: FastAPI inventory + variance tracking
- `services/sync`: Golang sync manager with offline replay
- `infra`: Docker Compose, k3s manifests, and ops artifacts
- `docs/contracts`: canonical contracts, state machines, RBAC, tax fields

## Local boot (MVP skeleton)

```bash
cd infra/docker
cp .env.example .env
docker compose up --build
```
