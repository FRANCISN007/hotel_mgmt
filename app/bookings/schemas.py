#CheckInSchema
from pydantic import BaseModel, root_validator
from typing import Optional, Literal
from datetime import date
from datetime import datetime



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
    payment_status: Optional[str] = "pending"  # Optional for check-ins
    number_of_days: Optional[int] = None  # Optional for input

    class Config:
        orm_mode = True
        
        
    @root_validator(pre=True)
    def calculate_number_of_days(cls, values):
        # Parse dates if they are strings
        arrival_date = values.get("arrival_date")
        departure_date = values.get("departure_date")
        if isinstance(arrival_date, str):
            arrival_date = datetime.strptime(arrival_date, "%Y-%m-%d").date()
            values["arrival_date"] = arrival_date
        if isinstance(departure_date, str):
            departure_date = datetime.strptime(departure_date, "%Y-%m-%d").date()
            values["departure_date"] = departure_date

        # Calculate the number of days
        if arrival_date and departure_date:
            values["number_of_days"] = (departure_date - arrival_date).days
        return values    
        

class BookingSchemaResponse(BaseModel):
    id: int
    room_number: str
    guest_name: str
    arrival_date: date
    departure_date: date
    booking_type: Literal["C", "R"]
    status: Optional[str] = "reserved"
    payment_status: Optional[str] = "pending"
    number_of_days: int  # Ensured as part of the response
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
