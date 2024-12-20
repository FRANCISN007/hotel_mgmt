from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.users.auth import get_current_user
from sqlalchemy.sql import func
from sqlalchemy import or_
from sqlalchemy import and_
from app.rooms import schemas as room_schemas, models as room_models, crud
from app.bookings import models as booking_models  # Adjust path if needed
from app.users import schemas
from datetime import date
from loguru import logger


router = APIRouter()



logger.add("app.log", rotation="500 MB", level="DEBUG")

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
    rooms = crud.get_rooms_with_pagination(skip=skip, limit=limit, db=db)
    
    # Convert SQLAlchemy rows to dictionaries
    serialized_rooms = crud.serialize_rooms(rooms)
    
    # Get the total count of rooms
    total_rooms = crud.get_total_room_count(db=db)
    
    # Return the response as a dictionary
    return {
        "total_rooms": total_rooms,  # Total number of rooms in the hotel
        "rooms": serialized_rooms,   # List of rooms
    }

@router.get("/transactions", response_model=list[dict])
def history(
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user)
            
):
    """
    Lists all rooms along with their current and past transactions, including:
    - Reservations
    - Check-ins
    - Current status (available, reserved, or checked-in)
    """
    # Query all rooms
    all_rooms = db.query(room_models.Room).all()



    # Query all check-ins
    check_ins = db.query(
        booking_models.Booking.room_number,
        booking_models.Booking.guest_name,
        booking_models.Booking.arrival_date,
        booking_models.Booking.departure_date,
        booking_models.Booking.status
    ).all()

    # Build a list of transactions for each room
    transactions_map = {}


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
    List all available rooms:
    - A room is available if it is not checked in for today.
    - A room can be reserved for a future date but is still available for today.
    """
    today = date.today()

    # Fetch all rooms currently checked in for today
    checked_in_rooms_today = (
        db.query(booking_models.Booking.room_number)
        .filter(
            booking_models.Booking.status == "checked-in",
            booking_models.Booking.arrival_date <= today,
            booking_models.Booking.departure_date >= today
        )
        .distinct()
        .all()
    )

    # Extract room numbers currently checked in today
    checked_in_room_numbers = {room.room_number for room in checked_in_rooms_today}

    # Fetch all rooms from the database
    all_rooms = db.query(room_models.Room).all()

    # Filter out rooms that are checked in for today
    available_rooms = [
        room for room in all_rooms if room.room_number not in checked_in_room_numbers
    ]

    # Total rooms in the database
    total_rooms = len(all_rooms)

    # If no rooms are available, return a fully booked message
    if not available_rooms:
        return {
            "message": "We are fully booked! All rooms are currently occupied for today.",
            "total_rooms": total_rooms,
            "total_available_rooms": 0,
            "available_rooms": [],
        }

    # Serialize the available rooms for the response
    serialized_rooms = [
        {
            "room_number": room.room_number,
            "room_type": room.room_type,
            "amount": room.amount,
        }
        for room in available_rooms
    ]

    return {
        "total_rooms": total_rooms,
        "total_available_rooms": len(serialized_rooms),
        "available_rooms": serialized_rooms,
    }




@router.put("/{room_number}")
def update_room(
    room_number: str,
    room_update: room_schemas.RoomUpdateSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Fetch the room by the current room_number
    room = db.query(room_models.Room).filter(room_models.Room.room_number == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Prevent updates if the room is checked-in
    if room.status == "checked-in":
        raise HTTPException(
            status_code=400,
            detail="Room cannot be updated as it is currently checked-in"
        )

    # If a new room_number is provided, check for conflicts
    if room_update.room_number and room_update.room_number != room.room_number:
        existing_room = db.query(room_models.Room).filter(room_models.Room.room_number == room_update.room_number).first()
        if existing_room:
            raise HTTPException(status_code=400, detail="Room with this number already exists")
        room.room_number = room_update.room_number  # Update the room number

    # Update other fields only if provided
    if room_update.room_type:
        room.room_type = room_update.room_type

    if room_update.amount is not None:
        room.amount = room_update.amount

    if room_update.status:
        if room_update.status not in ["available", "booked", "maintenance", "reserved"]:
            raise HTTPException(status_code=400, detail="Invalid status value")
        room.status = room_update.status

    # Commit the changes to the database
    db.commit()
    db.refresh(room)

    return {"message": "Room updated successfully", "room": room}



@router.get("/summary")
def room_summary(
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Generate a summary of all rooms, including counts of:
    - Checked-in rooms
    - Reserved rooms (both today and future, counted separately)
    - Available rooms for today
    """
    today = date.today()

    try:
        # Total number of rooms
        total_rooms = db.query(room_models.Room).count()

        # Checked-in rooms today
        total_checked_in_rooms = (
            db.query(booking_models.Booking)
            .filter(
                booking_models.Booking.status == "checked-in",
                booking_models.Booking.arrival_date <= today,
                booking_models.Booking.departure_date >= today,
            )
            .count()
        )

        # Reserved rooms (count reservations separately)
        total_reserved_rooms = (
            db.query(booking_models.Booking)
            .filter(
                booking_models.Booking.status == "reserved",
                booking_models.Booking.arrival_date >= today,
            )
            .count()
        )

        # Occupied rooms today (checked-in + reserved for today)
        occupied_rooms_today = (
            db.query(booking_models.Booking.room_number)
            .filter(
                or_(
                    booking_models.Booking.status == "checked-in",
                    and_(
                        booking_models.Booking.status == "reserved",
                        booking_models.Booking.arrival_date <= today,
                        booking_models.Booking.departure_date >= today,
                    ),
                )
            )
            .distinct()
            .all()
        )
        occupied_room_numbers_today = {room.room_number for room in occupied_rooms_today}

        # Total available rooms
        total_available_rooms = total_rooms - len(occupied_room_numbers_today)

        # Determine the appropriate message
        message = (
            f"{total_available_rooms} room(s) available."
            if total_available_rooms > 0
            else "Fully booked! All rooms are occupied for today."
        )

        return {
            "total_rooms": total_rooms,
            "rooms_checked_in": total_checked_in_rooms,
            "rooms_reserved": total_reserved_rooms,
            "rooms_available": total_available_rooms,
            "message": message,
        }

    except Exception as e:
        logger.error(f"Error generating room summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching room summary: {str(e)}",
        )



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

