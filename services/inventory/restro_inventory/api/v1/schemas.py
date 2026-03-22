"""Pydantic DTOs for inventory API."""

from pydantic import BaseModel, Field


class StockAdjustmentBody(BaseModel):
    ingredient_id: str = Field(..., min_length=1)
    delta_qty: float
    unit: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    actor_id: str = Field(..., min_length=1)


class TheoreticalConsumptionBody(BaseModel):
    kot_ticket_id: str = Field(..., min_length=1)
    ingredient_id: str = Field(..., min_length=1)
    consumed_qty: float
    unit: str = Field(..., min_length=1)
