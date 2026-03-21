# Restro Medha MVP Monorepo

Restro Medha is an offline-first restaurant system built for reliability in low or unstable internet environments.

This repository contains the MVP implementation with local-first billing, kitchen workflow, sync replay, and edge deployment tooling.

## What Is Inside This Repo

- `apps/pos` - Next.js POS and manager dashboard UI
- `apps/handheld` - React Native handheld app (waiter/kitchen flow shell)
- `services/gateway` - Golang API gateway with RBAC routing
- `services/billing` - FastAPI billing service (GST-ready fields + append-only ledger)
- `services/inventory` - FastAPI inventory and variance event logging
- `services/sync` - Golang sync manager (event ingest + replay + dedupe)
- `infra/docker` - Docker Compose setup for local edge stack
- `infra/k8s` - k3s deployment starter manifest
- `docs/contracts` - domain model, state machine, API/event contracts, RBAC
- `docs/runbooks` - deployment, incident response, and pilot acceptance checklists
- `tests/resilience` - dry-run script for end-to-end resilience smoke test

---

## Quick Start (For Beginners)

If you are new, follow this section exactly.

### 1) Install Prerequisites

Install these tools first:

- Git
- Docker Engine + Docker Compose plugin
- `curl`
- Python 3.10+ (used by test scripts)

Check installation:

```bash
git --version
docker --version
docker compose version
curl --version
python3 --version
```

### 2) Clone The Project

```bash
git clone <YOUR_REPO_URL>
cd Restro_Medha
```

### 3) Start The Full Local Stack

```bash
cp infra/docker/.env.example infra/docker/.env
docker compose -f infra/docker/docker-compose.yml up --build -d
```

This starts:

- Gateway on `http://localhost:8080`
- Billing on `http://localhost:8001`
- Inventory on `http://localhost:8002`
- Sync on `http://localhost:8003`

### 4) Verify Services Are Running

```bash
docker compose -f infra/docker/docker-compose.yml ps
curl -s http://localhost:8080/health
```

Expected health response:

```json
{"status":"ok"}
```

### 5) Run Dry-Run Test (Recommended)

This simulates order -> bill -> sync replay.

```bash
./tests/resilience/test_resilience.sh
```

Expected output:

```text
Resilience smoke tests passed
```

### 6) Check Revenue Report After Dry Run

```bash
curl -s http://localhost:8080/reports/revenue -H "X-Role: manager"
```

You should see JSON with `total_bills`, `gross_revenue`, and `top_selling_items`.

---

## Run The Apps (Optional, UI Development)

The backend works via Docker already. If you want to run frontend apps too:

### POS (Next.js)

```bash
cd apps/pos
npm install
NEXT_PUBLIC_GATEWAY_URL=http://localhost:8080 npm run dev
```

Open: [http://localhost:3000](http://localhost:3000)

### Handheld (React Native / Expo)

```bash
cd apps/handheld
npm install
EXPO_PUBLIC_GATEWAY_URL=http://localhost:8080 npm run start
```

Follow Expo instructions to open on emulator or phone.

---

## Common Commands

### Stop stack

```bash
docker compose -f infra/docker/docker-compose.yml down
```

### Stop stack and remove volumes (clears local DB data)

```bash
docker compose -f infra/docker/docker-compose.yml down -v
```

### View logs

```bash
docker compose -f infra/docker/docker-compose.yml logs -f
```

### Rebuild after code changes

```bash
docker compose -f infra/docker/docker-compose.yml up --build -d
```

---

## Backup and Restore (Edge Data)

### Create encrypted backup

```bash
export BACKUP_PASSPHRASE="your-strong-passphrase"
./scripts/backup.sh ./data ./backups
```

### Restore backup

```bash
export BACKUP_PASSPHRASE="your-strong-passphrase"
./scripts/restore.sh <path-to-backup-file.enc> ./data
```

---

## Troubleshooting

- Port already in use:
  - Stop old containers or processes on `8080`, `8001`, `8002`, `8003`.
- Docker permission errors:
  - Ensure your user has Docker access (`docker` group) or use `sudo` as per your setup.
- Health check fails:
  - Run `docker compose -f infra/docker/docker-compose.yml logs -f` and inspect failing service.
- Dry-run fails:
  - Ensure gateway is reachable: `curl -s http://localhost:8080/health`.
  - Then retry `./tests/resilience/test_resilience.sh`.

---

## Project Status

This is an MVP baseline focused on:

- local-first reliability
- GST-aligned billing fields
- KDS and sync workflow skeleton
- edge deployment readiness

AI forecasting, vision intelligence, and advanced multi-outlet intelligence are planned for later phases.
