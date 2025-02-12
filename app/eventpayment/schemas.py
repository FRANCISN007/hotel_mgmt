from pydantic import BaseModel
from typing import Optional
from datetime import date

# Base Schema for EventPayment
class EventPaymentBase(BaseModel):
    event_id: int
    organiser: str
    amount_paid: float
    discount_allowed: float = 0.0
    payment_method: str
    payment_status: Optional[str] = "pending"
    created_by: str

    class Config:
        from_attributes = True  # Replaces `orm_mode = True` for newer Pydantic versions

# Schema for Creating an Event Payment
class EventPaymentCreate(EventPaymentBase):
    pass

# Schema for Response when Retrieving an Event Payment
class EventPaymentResponse(EventPaymentBase):
    id: int
    balance_due: float
    payment_date: date
