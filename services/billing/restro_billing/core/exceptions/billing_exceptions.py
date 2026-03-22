"""
File: billing_exceptions.py
Purpose: Billing / invoice domain errors.
Responsibilities: Isolate bill creation failures from generic HTTP errors.
"""

from restro_billing.core.exceptions.base_exception import DomainException


class BillCreationException(DomainException):
    """Raised when a bill cannot be created from the current order state."""

    error_code = "BILL_CREATION_FAILED"
    http_status = 400
