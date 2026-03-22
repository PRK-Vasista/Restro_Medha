# restro-observability

Shared **JSON structured logging** and **request/tenant correlation** (`contextvars`) for Restro Medha Python microservices.

## Install

From repository root:

```bash
pip install ./libs/observability
```

Docker images install this package before service `requirements.txt`.

## Usage

```python
from restro_observability import configure_logging, get_logger, request_id_ctx, tenant_id_ctx

configure_logging(service_name="billing", log_json=True)
log = get_logger(__name__)
log.info("hello", extra={"method_name": "foo", "layer": "service", "status": "success"})
```
