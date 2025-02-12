from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Base Event Schema
class EventBase(BaseModel):
    organizer: str
    title: str
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    event_amount: float
    caution_fee: float
    location: Optional[str] = None
    phone_number: str
    address: str
    status: Optional[str] = "active"
    created_by: Optional[str] = None

    class Config:
        from_attributes = True  # Replaces `orm_mode = True` for newer Pydantic versions

# Schema for Creating an Event
class EventCreate(EventBase):
    pass

# Schema for Response when Retrieving an Event
class EventResponse(EventBase):
    id: int
    created_at: datetime
    updated_at: datetime
