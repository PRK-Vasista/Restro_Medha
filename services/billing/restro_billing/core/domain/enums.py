"""
File: enums.py
Purpose: Domain enumerations (no business logic).
Responsibilities: Canonical workflow states for orders, bills, and kitchen tickets.
"""

from enum import Enum


class OrderState(str, Enum):
    """
    Class: OrderState
    Description: Dine-in order lifecycle states for the sales aggregate.

    Attributes:
        Enum members only (placed, in_prep, ready, served, cancelled).

    Example usage:
        current = OrderState.placed
    """

    placed = "placed"
    in_prep = "in_prep"
    ready = "ready"
    served = "served"
    cancelled = "cancelled"


class BillState(str, Enum):
    """
    Class: BillState
    Description: Financial settlement states for an invoice aggregate.

    Attributes:
        draft, finalized, paid.

    Example usage:
        BillState.finalized
    """

    draft = "draft"
    finalized = "finalized"
    paid = "paid"


class KotState(str, Enum):
    """
    Class: KotState
    Description: Kitchen ticket progression.

    Attributes:
        queued, acknowledged, preparing, complete.

    Example usage:
        KotState.preparing
    """

    queued = "queued"
    acknowledged = "acknowledged"
    preparing = "preparing"
    complete = "complete"


class UserRole(str, Enum):
    """
    Class: UserRole
    Description: Reference roles for documentation; enforcement lives in gateway + optional service checks.

    Attributes:
        manager, cashier, kitchen_staff.

    Example usage:
        UserRole.manager.value
    """

    manager = "manager"
    cashier = "cashier"
    kitchen_staff = "kitchen_staff"
