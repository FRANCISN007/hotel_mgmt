from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.users.auth import get_current_user
from sqlalchemy.sql import func
#from . import schemas, models, crud  # Import room-specific schemas, models, and CRUD
from sqlalchemy import or_
from app.rooms import models
from app.reservations import models
#from app.rooms import schemas, models, crud  # Import room-specific schemas, models, and CRUD
from app.rooms import schemas as room_schemas, models as room_models, crud

from app.rooms import models as room_models, schemas
from app.reservations import models as reservation_models
from app.guest import models as check_in_models  # Adjust path if needed
from app.users import schemas
router = APIRouter()


@router.post("/")
def create_room(
    room: schemas.RoomSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    existing_room = db.query(room_models.Room).filter(room_models.Room.room_number == room.room_number).first()
    if existing_room:
        raise HTTPException(status_code=400, detail="Room with this number already exists")

    new_room = crud.create_room(db, room)
    return {"message": "Room created successfully", "room": new_room}


@router.get("/", response_model=dict)
def list_rooms(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    Fetch a list of rooms with basic details: room number, room type, and amount.
    Also include the total number of rooms in the hotel.
    """
    # Fetch the list of rooms with pagination
    rooms = (
        db.query(room_models.Room.room_number, room_models.Room.room_type, room_models.Room.amount)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Convert SQLAlchemy rows to dictionaries
    serialized_rooms = [
        {
            "room_number": room.room_number,
            "room_type": room.room_type,
            "amount": room.amount,
        }
        for room in rooms
    ]
    
    # Get the total count of rooms
    total_rooms = db.query(room_models.Room).count()
    
    # Return the response as a dictionary
    return {
        "total_rooms": total_rooms,  # Total number of rooms in the hotel
        "rooms": serialized_rooms,   # List of rooms
    }


@router.get("/transactions", response_model=list[dict])
def history(db: Session = Depends(get_db)):
    """
    Lists all rooms along with their current and past transactions, including:
    - Reservations
    - Check-ins
    - Current status (available, reserved, or checked-in)
    """
    # Query all rooms
    all_rooms = db.query(room_models.Room).all()

    # Query all reservations
    reservations = db.query(
        reservation_models.Reservation.room_number,
        reservation_models.Reservation.guest_name,
        reservation_models.Reservation.arrival_date,
        reservation_models.Reservation.departure_date,
        reservation_models.Reservation.status
    ).all()

    # Query all check-ins
    check_ins = db.query(
        check_in_models.Check_in.room_number,
        check_in_models.Check_in.guest_name,
        check_in_models.Check_in.arrival_date,
        check_in_models.Check_in.departure_date,
        check_in_models.Check_in.status
    ).all()

    # Build a list of transactions for each room
    transactions_map = {}

    # Map reservations
    for res in reservations:
        if res.room_number not in transactions_map:
            transactions_map[res.room_number] = []
        transactions_map[res.room_number].append({
            "transaction_type": "reservation",
            "guest_name": res.guest_name,
            "arrival_date": res.arrival_date,
            "departure_date": res.departure_date,
            "status": res.status
        })

    # Map check-ins
    for check_in in check_ins:
        if check_in.room_number not in transactions_map:
            transactions_map[check_in.room_number] = []
        transactions_map[check_in.room_number].append({
            "transaction_type": "check-in",
            "guest_name": check_in.guest_name,
            "arrival_date": check_in.arrival_date,
            "departure_date": check_in.departure_date,
            "status": check_in.status
        })

    # Prepare the response with all room details and transactions
    result = []
    for room in all_rooms:
        room_data = {
            "room_number": room.room_number,
            "room_type": room.room_type,
            "amount": room.amount,
            "current_status": room.status,
            "transactions": transactions_map.get(room.room_number, [])
        }
        result.append(room_data)

    return result




@router.get("/available")
def list_available_rooms(db: Session = Depends(get_db)):
    """
    List all available rooms. If no rooms are available, return a message stating the hotel is fully booked.
    """
    # Query for rooms with 'available' status
    available_rooms = db.query(room_models.Room).filter(room_models.Room.status == "available").all()
    
    # Count the total number of rooms
    total_rooms = db.query(room_models.Room).count()
    
    # If no available rooms, display fully booked message
    if not available_rooms:
        return {
            "message": "We are fully booked!",
            "total_rooms": total_rooms,
            "total_available_rooms": 0,
            "available_rooms": []
        }

    # Return the list of available rooms and their count
    return {
        "total_rooms": total_rooms,
        "total_available_rooms": len(available_rooms),
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

    room = db.query(room_models.Room).filter(room_models.Room.room_number == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Prevent updates if the room is checked-in
    if room.status == "checked-in":
        raise HTTPException(
            status_code=400,
            detail="Room cannot be updated as it is currently checked-in"
        )

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
    total_rooms = db.query(room_models.Room).count()
    total_checked_in_rooms = db.query(room_models.Room).filter(room_models.Room.status == "checked-in").count()
    total_reserved_rooms = db.query(room_models.Room).filter(room_models.Room.status == "reserved").count()
    total_available_rooms = db.query(room_models.Room).filter(room_models.Room.status == "available").count()

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
    # Ensure only admin can delete rooms
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Fetch the room by room_number
    room = db.query(room_models.Room).filter(room_models.Room.room_number == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Prevent deletion of rooms with status 'checked-in' or 'reserved'
    if room.status in ["checked-in", "reserved"]:
        raise HTTPException(
            status_code=400,
            detail=f"Room {room_number} cannot be deleted as it is currently {room.status}."
        )

    # Delete the room if it is available
    try:
        db.delete(room)
        db.commit()
        return {"message": f"Room {room_number} deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while deleting the room: {str(e)}"
        )

