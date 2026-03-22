"""
File: revenue_service.py
Purpose: Read-model analytics use cases (business logic layer).
Responsibilities: Aggregate revenue and top SKUs per tenant.
"""

from __future__ import annotations

from typing import Any

from restro_observability import get_logger
from restro_billing.core.protocols.billing_storage import BillingStoragePort

logger = get_logger(__name__)


class RevenueReportService:
    """
    Class: RevenueReportService
    Description: Builds revenue summaries from persisted bills.

    Attributes:
        _storage: Persistence port.

    Example usage:
        RevenueReportService(store).build_report(tenant_id)
    """

    def __init__(self, storage: BillingStoragePort) -> None:
        self._storage = storage

    def build_report(self, tenant_id: str) -> dict[str, Any]:
        """
        Description: Compute totals and top-selling lines for dashboards.

        Inputs:
            tenant_id: SaaS tenant scope.

        Outputs:
            dict: {total_bills, gross_revenue, top_selling_items}

        Exceptions raised:
            None
        """
        logger.info(
            "revenue_report_enter",
            extra={"method_name": "build_report", "layer": "service", "status": "pending"},
        )
        total_bills, gross, top = self._storage.revenue_aggregates(tenant_id)
        out = {
            "total_bills": total_bills,
            "gross_revenue": gross,
            "top_selling_items": top,
        }
        logger.info(
            "revenue_report_exit",
            extra={"method_name": "build_report", "layer": "service", "status": "success"},
        )
        return out
