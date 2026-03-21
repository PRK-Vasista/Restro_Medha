# Deployment Runbook (Edge)

## Prerequisites
- Edge server with Docker and Compose plugin.
- Local network access from POS and handheld devices.
- TLS certificates provisioned in `infra/certs`.

## Deploy
1. Pull latest images from registry.
2. Update `infra/docker/.env` as needed.
3. Run `docker compose -f infra/docker/docker-compose.yml up -d`.
4. Validate `http://<edge-ip>:8080/health`.

## Rollback
1. Identify previous known-good tags.
2. Pin image tags in compose file.
3. Redeploy with `docker compose up -d`.
4. Validate health and run `tests/resilience/test_resilience.sh`.
