from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PaymentCreateSchema(BaseModel):
    guest_name: str
    room_number: str
    amount_paid: float
    discount_allowed: Optional[float] = 0.0  # New discount field, default to 0.0
    payment_method: str  # E.g., 'credit_card', 'cash', 'bank_transfer'
    payment_date: Optional[datetime] = None  # Defaults to current datetime if not provided
    balance_due: Optional[float] = 0.0 
    status: Optional[str] = "pending"  # Payment status (e.g., pending, completed, failed)

    class Config:
        orm_mode = True


class PaymentUpdateSchema(BaseModel):
    """
    Schema to update payment details.
    """
    guest_name: str
    room_number: str
    amount_paid: Optional[float] = None  # Update the amount if provided
    discount_allowed: Optional[float] = None  # Update discount if provided
    payment_method: Optional[str] = None  # Update the payment method if provided
    payment_date: Optional[datetime] = None  # Update the payment date if provided
    status: Optional[str] = None  # Update the status (e.g., 'completed', 'pending') if provided

    class Config:
        orm_mode = True
