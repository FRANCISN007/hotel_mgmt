from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.users.auth import get_current_user
from sqlalchemy.sql import func
#from . import schemas, models, crud  # Import room-specific schemas, models, and CRUD
from sqlalchemy import or_
from app.rooms import models
from app.reservations import models
from app.rooms import schemas, models, crud  # Import room-specific schemas, models, and CRUD

router = APIRouter()


@router.post("/")
def create_room(
    room: schemas.RoomSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    existing_room = db.query(models.Room).filter(models.Room.room_number == room.room_number).first()
    if existing_room:
        raise HTTPException(status_code=400, detail="Room with this number already exists")

    new_room = crud.create_room(db, room)
    return {"message": "Room created successfully", "room": new_room}


@router.get("/", response_model=list[schemas.RoomSchema])
def list_rooms(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    rooms = db.query(models.Room).offset(skip).limit(limit).all()
    return rooms


@router.get("/available")
def list_available_rooms(db: Session = Depends(get_db)):
    available_rooms = db.query(models.Room).filter(models.Room.status == "available").all()
    total_available_rooms = len(available_rooms)

    if total_available_rooms == 0:
        return {
            "message": "We are fully booked!",
            "total_available_rooms": 0,
            "available_rooms": []
        }

    return {
        "total_available_rooms": total_available_rooms,
        "available_rooms": available_rooms
    }


@router.put("/{room_number}")
def update_room(
    room_number: str,
    room_update: schemas.RoomUpdateSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    room = db.query(models.Room).filter(models.Room.room_number == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Update fields only if provided
    if room_update.room_type:
        room.room_type = room_update.room_type

    if room_update.amount is not None:
        room.amount = room_update.amount

    if room_update.status:
        if room_update.status not in ["available", "booked", "maintenance"]:
            raise HTTPException(status_code=400, detail="Invalid status value")
        room.status = room_update.status

    db.commit()
    db.refresh(room)

    return {"message": "Room updated successfully", "room": room}


@router.get("/summary")
def room_summary(
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    total_rooms = db.query(models.Room).count()
    total_checked_in_rooms = db.query(models.Room).filter(models.Room.status == "checked-in").count()
    total_reserved_rooms = db.query(models.Room).filter(models.Room.status == "reserved").count()
    total_available_rooms = db.query(models.Room).filter(models.Room.status == "available").count()

    message = "Fully booked!" if total_available_rooms == 0 else f"{total_available_rooms} room(s) available."

    return {
        "total_rooms": total_rooms,
        "rooms_checked_in": total_checked_in_rooms,
        "rooms_reserved": total_reserved_rooms,
        "rooms_available": total_available_rooms,
        "message": message,
    }


@router.delete("/{room_number}")
def delete_room(
    room_number: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    room = db.query(models.Room).filter(models.Room.room_number == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    db.delete(room)
    db.commit()

    return {"message": f"Room with room number {room_number} has been deleted successfully"}
