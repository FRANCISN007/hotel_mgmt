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


from pydantic import BaseModel
from typing import Literal

from pydantic import BaseModel
from typing import Literal

class RoomSchema(BaseModel):
    room_number: str
    room_type: str
    amount: float
    status: Literal["available", "checked-in", "maintenance", "reserved"]  # Updated status options

    class Config:
        orm_mode = True


        
class RoomUpdateSchema(BaseModel):
    room_type: Optional[str] = None
    amount: Optional[int] = None
    status: Optional[Literal["available", "booked", "maintenance", "reserved"]] = None

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
