from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.events import models as event_models
from app.events import schemas as event_schemas
from app.users import schemas as user_schemas
from app.users.auth import get_current_user


router = APIRouter()

# Create Event
@router.post("/", response_model=event_schemas.EventResponse)
def create_event(
    event: event_schemas.EventCreate, 
    db: Session = Depends(get_db), 
    current_user: user_schemas.UserDisplaySchema = Depends(get_current_user),
):
    db_event = event_models.Event(
        organizer=event.organizer,
        title=event.title,
        description=event.description,
        start_datetime=event.start_datetime,
        end_datetime=event.end_datetime,
        event_amount=event.event_amount,
        caution_fee=event.caution_fee,
        location=event.location,
        phone_number=event.phone_number,
        address=event.address,
        status=event.status or "active",
        created_by=current_user.username
    )

    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


# List Events with Filters (Start Date, End Date, Created By)
@router.get("/", response_model=List[event_schemas.EventResponse])
def list_events(
    db: Session = Depends(get_db),
    current_user: user_schemas.UserDisplaySchema = Depends(get_current_user),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
   
):
    query = db.query(event_models.Event)

    if start_date:
        query = query.filter(event_models.Event.start_datetime >= start_date)
    if end_date:
        query = query.filter(event_models.Event.end_datetime <= end_date)

    events = query.order_by(event_models.Event.start_datetime).all()
    return events


# Get Event by ID
@router.get("/{event_id}", response_model=event_schemas.EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    db_event = db.query(event_models.Event).filter(event_models.Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    return db_event


# Update Event (Only Creator or Admin)
@router.put("/{event_id}", response_model=dict)
def update_event(
    event_id: int,
    event: event_schemas.EventCreate, 
    db: Session = Depends(get_db), 
    current_user: user_schemas.UserDisplaySchema = Depends(get_current_user),
):
    db_event = db.query(event_models.Event).filter(event_models.Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    if db_event.created_by != current_user.username and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only event creators or admins can update events")

    for field, value in event.dict(exclude_unset=True).items():
        setattr(db_event, field, value)

    db.commit()
    db.refresh(db_event)

    return {"message": "Event updated successfully"}


# Cancel Event (Only Admin, With Cancellation Reason)
@router.put("/{event_id}/cancel", response_model=dict)
def cancel_event(
    event_id: int, 
    cancellation_reason: str,
    db: Session = Depends(get_db), 
    current_user: user_schemas.UserDisplaySchema = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can cancel events")

    db_event = db.query(event_models.Event).filter(event_models.Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    db_event.status = "canceled"
    db_event.cancellation_reason = cancellation_reason  # Store reason in the column

    db.commit()
    db.refresh(db_event)  # Refresh the event to reflect changes in the session
    return {"message": "Event cancellation successful", "cancellation_reason": cancellation_reason}
