from pydantic import BaseModel
from typing import Optional, Literal
from datetime import date


class GuestReservationSchema(BaseModel):
    """
    Schema for a reservation record specific to guest operations.
    """
    room_number: str
    guest_name: str
    arrival_date: date
    departure_date: date
    status: Optional[str] = "reserved"

    class Config:
        orm_mode = True


class CheckInSchema(BaseModel):
    room_number: str
    guest_name: str
    arrival_date: date
    departure_date: date
    is_checked_out: bool = False
    payment_status: str = "pending"  # Default payment status
    
    class Config:
        orm_mode = True


class UserDisplaySchema(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        orm_mode = True
        

class CheckInUpdateSchema(BaseModel):
    room_number: str
    guest_name: str
    arrival_date: Optional[date]
    departure_date: Optional[date]
