#CheckInSchema
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

""""
class CheckInSchema(BaseModel):
    room_number: str
    guest_name: str
    arrival_date: date
    departure_date: date
    is_checked_out: bool = False
    payment_status: str = "pending"  # Default payment status
    
    class Config:
        orm_mode = True

"""



class BookingSchema(BaseModel):
    """
    Unified schema for both reservations and check-ins.
    """
    room_number: str
    guest_name: str
    arrival_date: date
    departure_date: date
    booking_type: Literal["C", "R"]
    #status: Optional[str] = "reserved"  # Default status
    payment_status: Optional[str] = "pending"  # Optional for check-ins
    #is_checked_out: Optional[bool] = False  # Optional, applies to check-ins only
    #cancellation_reason: Optional[str] = None  # Optional, applies to reservations only

    class Config:
        orm_mode = True

class BookingSchemaResponse(BaseModel):
    id: int
    room_number: str
    guest_name: str
    arrival_date: date
    departure_date: date
    booking_type: Literal["C", "R"]
    status: Optional[str] = "reserved"
    payment_status: Optional[str] = "pending"
    is_checked_out: Optional[bool] = False
    cancellation_reason: Optional[str] = None

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
