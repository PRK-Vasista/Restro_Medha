"""
File: schemas.py
Purpose: Pydantic request/response DTOs for the HTTP layer (not domain entities).
Responsibilities: Input validation at controller boundary; stable JSON shapes.
"""

from pydantic import BaseModel, Field, field_validator

from restro_billing.core.domain.enums import OrderState


class OrderLineIn(BaseModel):
    """
    Class: OrderLineIn
    Description: Validated line item for order creation.

    Attributes:
        item_id, item_name, qty, unit_price.

    Example usage:
        OrderLineIn(item_id="1", item_name="Dosa", qty=1, unit_price=100)
    """

    item_id: str = Field(..., min_length=1)
    item_name: str = Field(..., min_length=1)
    qty: float = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)


class CreateOrderBody(BaseModel):
    """HTTP body for POST /orders."""

    table_no: str | None = None
    lines: list[OrderLineIn] = Field(..., min_length=1)


class OrderStatePatchBody(BaseModel):
    """HTTP body for PATCH /orders/{id}/state."""

    state: OrderState


class CreateBillBody(BaseModel):
    """HTTP body for POST /bills."""

    order_id: str = Field(..., min_length=1)
    gstin: str | None = None

    @field_validator("gstin")
    @classmethod
    def strip_gstin(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        return s or None


class MenuItemIn(BaseModel):
    """Single row for bulk menu import."""

    item_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    hsn_code: str = Field(..., min_length=1)
    unit_price: float = Field(..., ge=0)


class BulkMenuImportBody(BaseModel):
    """HTTP body for POST /menu/import."""

    items: list[MenuItemIn] = Field(..., min_length=1)


class KdsStateBody(BaseModel):
    """HTTP body for PATCH /kds/tickets/{id}/state."""

    state: str = Field(..., min_length=1)
