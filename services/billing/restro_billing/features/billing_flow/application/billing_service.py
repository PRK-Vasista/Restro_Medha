"""
File: billing_service.py
Purpose: Bill finalization use cases (business logic layer).
Responsibilities: Compute GST split from config; persist bill + ledger; idempotency.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from restro_billing.config.settings import Settings
from restro_billing.core.domain.enums import BillState
from restro_billing.core.exceptions.order_exceptions import OrderNotFoundException
from restro_billing.core.logging.structured_logging import get_logger
from restro_billing.core.protocols.billing_storage import BillingStoragePort

logger = get_logger(__name__)


class BillingApplicationService:
    """
    Class: BillingApplicationService
    Description: Creates finalized bills from existing orders.

    Attributes:
        _storage: Persistence port.
        _settings: Contains gst_combined_rate.

    Example usage:
        svc.finalize_bill(tenant_id, order_id, gstin, idempotency_key)
    """

    def __init__(self, storage: BillingStoragePort, settings: Settings) -> None:
        self._storage = storage
        self._settings = settings

    def finalize_bill(
        self,
        tenant_id: str,
        order_id: str,
        gstin: str | None,
        idempotency_key: str | None,
    ) -> dict[str, Any]:
        """
        Description: Finalize invoice for an order (MVP: single combined GST rate).

        Inputs:
            tenant_id: SaaS tenant scope.
            order_id: Source order UUID.
            gstin: Optional buyer/seller GSTIN for invoice payload.
            idempotency_key: Optional dedupe key.

        Outputs:
            dict: {bill_id, state, grand_total}

        Exceptions raised:
            OrderNotFoundException: If order row missing.
        """
        logger.info(
            "finalize_bill_enter",
            extra={"method_name": "finalize_bill", "layer": "service", "status": "pending"},
        )
        endpoint = "/bills"
        if idempotency_key:
            cached = self._storage.get_idempotent_response(tenant_id, idempotency_key, endpoint)
            if cached is not None:
                return cached

        row = self._storage.get_order_row(tenant_id, order_id)
        if row is None:
            raise OrderNotFoundException(tenant_id, order_id)

        payload = row["payload"]
        lines = payload["lines"]
        subtotal = sum(float(line["qty"]) * float(line["unit_price"]) for line in lines)
        rate = self._settings.gst_combined_rate
        tax = round(subtotal * rate, 2)
        total = round(subtotal + tax, 2)
        bill_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        bill_payload = {
            "invoice_number": f"RM-{int(datetime.now().timestamp())}",
            "invoice_date_time": created_at,
            "gstin": gstin,
            "lines": lines,
            "subtotal": subtotal,
            "total_taxable_value": subtotal,
            "total_cgst": round(tax / 2, 2),
            "total_sgst": round(tax / 2, 2),
            "total_igst": 0.0,
            "grand_total": total,
        }
        self._storage.insert_bill(
            tenant_id,
            bill_id,
            order_id,
            BillState.finalized.value,
            subtotal,
            tax,
            total,
            gstin,
            bill_payload,
            created_at,
            bill_payload,
        )
        resp = {"bill_id": bill_id, "state": BillState.finalized.value, "grand_total": total}
        if idempotency_key:
            self._storage.save_idempotent_response(tenant_id, idempotency_key, endpoint, resp)
        logger.info(
            "finalize_bill_exit",
            extra={"method_name": "finalize_bill", "layer": "service", "status": "success"},
        )
        return resp
