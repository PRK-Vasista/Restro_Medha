"""
File: menu_exceptions.py
Purpose: Menu catalog domain errors (reserved for future validation rules).
Responsibilities: Placeholder module to keep exception taxonomy consistent.
"""

from restro_billing.core.exceptions.base_exception import DomainException


class MenuImportValidationException(DomainException):
    """Raised when bulk import payload violates domain rules."""

    error_code = "MENU_IMPORT_INVALID"
    http_status = 400
