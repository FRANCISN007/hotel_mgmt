from pydantic import BaseModel
from typing import List
from datetime import datetime
from typing import Optional
from typing import Literal
from decimal import Decimal

class UserSchema(BaseModel):
    username: str
    password: str
    role: str

    class Config:
        orm_mode = True
        
class UserDisplaySchema(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        orm_mode = True


class RoomSchema(BaseModel):
    room_number: str
    room_type: str
    amount: int
    status: Literal["available", "booked", "maintenance"]  # Only these values allowed
    
    class Config:
        orm_mode = True
        
class RoomUpdateSchema(BaseModel):
    room_type: Optional[str] = None
    amount: Optional[int] = None
    status: Optional[Literal["available", "booked", "maintenance"]] = None

    class Config:
        orm_mode = True


class ReservationSchema(BaseModel):
    room_number: str  # Use room_number instead of room_id
    guest_name: str
    arrival_date: datetime
    departure_date: datetime
    status: Optional[str] = "booked"  # Default value

    class Config:
        orm_mode = True

class CheckInSchema(BaseModel):
    room_number: str
    guest_name: str
    arrival_date: datetime
    departure_date: datetime

    class Config:
        orm_mode = True
