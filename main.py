import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi import Request
from auth import pwd_context, authenticate_user, create_access_token, get_current_user
import auth, crud, schemas, models
from database import get_db
#from models import Base, engine
from database import engine, Base, get_db
from sqlalchemy import and_
from datetime import datetime, date
from typing import List
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from schemas import UserDisplaySchema
from sqlalchemy.orm import aliased
#from logger import get_logger


#logger = get_logger(__name__)

app = FastAPI()

# Database initialization
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

#HMS_PASSWORD = os.environ.get('ADMIN_PASSWORD')
#ADMIN_PASSWORD = "pass"  # Replace with your actual admin password

@app.post("/register/", tags=["User"])
def register_user(user: schemas.UserSchema, db: Session = Depends(get_db)):
    # Check if the username already exists
    existing_user = crud.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check admin registration
    if user.role == "admin":
        if not user.admin_password or user.admin_password != ADMIN_PASSWORD:
            raise HTTPException(status_code=403, detail="Invalid admin password")

    # Hash the password and create the user
    hashed_password = auth.get_password_hash(user.password)
    crud.create_user(db, user, hashed_password)
    return {"message": "User registered successfully"}


@app.post("/token", tags= ["User"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


#@app.get("/users/", response_model=list[schemas.UserDisplaySchema], tags=["User"])
#def list_all_users(db: Session = Depends(get_db), skip: int = 0, limit: int = 10):
    #users = crud.get_all_users(db)
    #return users
    
@app.get("/users/", response_model=list[schemas.UserDisplaySchema], tags=["User"])
def list_all_users(
    db: Session = Depends(get_db), 
    skip: int = 0, 
    limit: int = 10, 
    current_user: schemas.UserDisplaySchema = Depends(get_current_user)
):
    # Only allow admin users to delete other users
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    users = crud.get_all_users(db)
    return users

@app.delete("/users/{username}", tags=["User"])
def delete_user(
    username: str, 
    db: Session = Depends(get_db), 
    current_user: schemas.UserDisplaySchema = Depends(get_current_user)
):
    # Only allow admin users to delete other users
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": f"User {username} deleted successfully"}
 

@app.post("/rooms/", tags=["Rooms"])
def create_room(
    room: schemas.RoomSchema, 
    db: Session = Depends(get_db), 
    current_user: schemas.UserDisplaySchema = Depends(get_current_user)
):
    # Optional: Check if the user has sufficient permissions based on `current_user.role`
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    existing_room = db.query(models.Room).filter(models.Room.room_number == room.room_number).first()
    if existing_room:
        raise HTTPException(status_code=400, detail="Room with this number already exists")
    new_room = crud.create_room(db, room)
    return {"message": "Room created successfully", "room": new_room}

    
@app.get("/rooms/", response_model=list[schemas.RoomSchema], tags=["Rooms"])
def list_rooms(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    rooms = db.query(models.Room).offset(skip).limit(limit).all()
    return rooms
    
@app.get("/rooms/available", tags=["Rooms"])
def list_available_rooms(
    db: Session = Depends(get_db)
):
    # Query all available rooms
    available_rooms = db.query(models.Room).filter(models.Room.status == "available").all()
    total_available_rooms = len(available_rooms)  # Total number of available rooms
    
    # Check if no rooms are available
    if total_available_rooms == 0:
        return {
            "message": "We are fully booked!",
            "total_available_rooms": 0,
            "available_rooms": []
        }
    
    # Return all available rooms and the total count
    return {
        
        "total_available_rooms": total_available_rooms,
        "available_rooms": available_rooms
    }

@app.post("/check-in/", tags=["Guests"])
def check_in_guest(
    check_in_request: schemas.CheckInSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user)
):
    """
    Check a guest into a room.
    Ensures no duplicate check-ins occur for the same room.
    """
    room_number = check_in_request.room_number

    # Check if the room exists
    room = db.query(models.Room).filter(models.Room.room_number == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Check if the room already has a checked-in reservation
    existing_reservation = (
        db.query(models.Reservation)
        .filter(
            models.Reservation.room_number == room_number,
            models.Reservation.status == "checked-in"
        )
        .first()
    )
    if existing_reservation:
        raise HTTPException(
            status_code=400,
            detail=f"Room {room_number} is already checked in by {existing_reservation.guest_name}"
        )

    # Ensure the room is available
    if room.status != "available":
        raise HTTPException(status_code=400, detail="Room is not available for check-in")

    try:
        # Create the reservation and mark it as "checked-in"
        new_reservation = models.Reservation(
            room_number=room_number,
            guest_name=check_in_request.guest_name,
            arrival_date=check_in_request.arrival_date,
            departure_date=check_in_request.departure_date,
            status="checked-in",
        )
        db.add(new_reservation)

        # Update the room status to "checked-in"
        room.status = "checked-in"

        # Commit the changes to the database
        db.commit()
        db.refresh(new_reservation)

        return {
            "message": f"Guest {check_in_request.guest_name} successfully checked into room {room_number}",
            "reservation": {
                "guest_name": new_reservation.guest_name,
                "room_number": new_reservation.room_number,
                "arrival_date": new_reservation.arrival_date,
                "departure_date": new_reservation.departure_date,
                "status": new_reservation.status
            }
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")



@app.get("/guests/checked-in", tags=["Guests"])
def list_checked_in_guests(db: Session = Depends(get_db)):
    """
    List all guests currently checked into rooms, along with their room numbers
    and check-in/check-out dates.
    """
    try:
        # Query for guests who are currently checked in
        checked_in_guests = (
            db.query(
                models.Reservation.guest_name,
                models.Reservation.room_number,
                func.date(models.Reservation.arrival_date).label("check_in_date"),
                func.date(models.Reservation.departure_date).label("departure_date")
            )
            .filter(models.Reservation.status == "checked-in")
            .all()
        )

        # If no guests are checked in, return a message
        if not checked_in_guests:
            return {"message": "No guests are currently checked in."}

        # Format the response
        return {
            "total_checked_in_guests": len(checked_in_guests),
            "checked_in_guests": [
                {
                    "guest_name": guest.guest_name,
                    "room_number": guest.room_number,
                    "check_in_date": guest.check_in_date,
                    "departure_date": guest.departure_date,
                }
                for guest in checked_in_guests
            ],
        }

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving checked-in guests: {str(e)}"
        )



@app.put("/rooms/{room_number}", tags=["Rooms"])
def update_room(
    room_number: str,
    room_update: schemas.RoomUpdateSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    # Proceed with the rest of the update logic

    # Fetch the room by its room_number
    room = db.query(models.Room).filter(models.Room.room_number == room_number).first()

    # If the room does not exist, raise a 404 error
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

    # Commit changes to the database
    db.commit()
    db.refresh(room)

    # Return the updated room details
    return {"message": "Room updated successfully", "room": room}

@app.get("/rooms/summary", tags=["Rooms"])
def room_summary(
    db: Session = Depends(get_db), 
    current_user: schemas.UserDisplaySchema = Depends(get_current_user)
):
    # Query total rooms
    total_rooms = db.query(models.Room).count()
    
    # Query checked-in rooms
    total_checked_in_rooms = db.query(models.Room).filter(models.Room.status == "checked-in").count()
    
    # Query reserved rooms
    total_reserved_rooms = db.query(models.Room).filter(models.Room.status == "reserved").count()
    
    # Query available rooms
    total_available_rooms = db.query(models.Room).filter(models.Room.status == "available").count()
    
    # Determine message based on availability
    message = "Fully booked!" if total_available_rooms == 0 else f"{total_available_rooms} room(s) available."
    
    # Return summary
    return {
        "total_rooms": total_rooms,
        "rooms_checked_in": total_checked_in_rooms,
        "rooms_reserved": total_reserved_rooms,
        "rooms_available": total_available_rooms,
        "message": message
    }


@app.delete("/rooms/{room_number}", tags=["Rooms"])
def delete_room(
    room_number: str, 
    db: Session = Depends(get_db), 
    current_user: schemas.UserDisplaySchema = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    # Proceed with the delete logic

    # Fetch the room by its room_number
    room = db.query(models.Room).filter(models.Room.room_number == room_number).first()

    # If the room does not exist, raise a 404 error
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Delete the room from the database
    db.delete(room)
    db.commit()

    # Return a success message
    return {"message": f"Room with room number {room_number} has been deleted successfully"}



@app.get("/reserved", tags=["Reservations"])
def list_reserved_rooms(db: Session = Depends(get_db)):
    # Query reserved rooms and include arrival and departure dates
    reserved_rooms = (
        db.query(
            models.Room.room_number,
            models.Room.room_type,
            models.Reservation.guest_name,
            models.Reservation.arrival_date,
            models.Reservation.departure_date
        )
        .join(models.Reservation, models.Room.room_number == models.Reservation.room_number)
        .filter(models.Room.status == "reserved")
        .all()
    )
    
    # Count the number of reserved rooms
    total_reserved_rooms = len(reserved_rooms)
    
    # Return reserved rooms and the total count
    return {
        "total_reserved_rooms": total_reserved_rooms,
        "reserved_rooms": [
            {
                "room_number": room.room_number,
                "room_type": room.room_type,
                "guest_name": room.guest_name,
                "arrival_date": room.arrival_date,
                "departure_date": room.departure_date,
            }
            for room in reserved_rooms
        ]
    }


@app.post("/reservations/", tags=["Reservations"])
def create_reservation(reservation: schemas.ReservationSchema, db: Session = Depends(get_db)):
    # Ensure all required fields are provided
    if not reservation.room_number or not reservation.guest_name:
        raise HTTPException(status_code=400, detail="Room number and guest name are required.")

    # Check if the room exists
    room = db.query(models.Room).filter(models.Room.room_number == reservation.room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Check if the room is available for reservation
    if room.status != "available":
        raise HTTPException(status_code=400, detail=f"Room {reservation.room_number} is not available for reservation.")

    # Ensure no conflicting reservations exist
    existing_reservation = db.query(models.Reservation).filter(
        models.Reservation.room_number == reservation.room_number,
        models.Reservation.arrival_date <= reservation.departure_date,  # Overlap condition
        models.Reservation.departure_date >= reservation.arrival_date,  # Overlap condition
    ).first()

    if existing_reservation:
        raise HTTPException(
            status_code=400,
            detail=f"Room {reservation.room_number} already reserved from {existing_reservation.arrival_date} "
                   f"to {existing_reservation.departure_date}."
        )

    # Proceed with creating the reservation
    try:
        new_reservation = models.Reservation(
            room_number=reservation.room_number,
            guest_name=reservation.guest_name,
            arrival_date=reservation.arrival_date,
            departure_date=reservation.departure_date,
            status="reserved",
        )
        db.add(new_reservation)
        db.commit()
        db.refresh(new_reservation)

        # Update room status to "reserved"
        room.status = "reserved"
        db.commit()

        return {"message": "Reservation created successfully", "reservation": new_reservation}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")




@app.put("/check-out-group/", tags=["Reservations"])
def check_out_multiple_rooms(
    room_numbers: list[str],  # Accept a list of room numbers
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user)
):
    results = []

    for room_number in room_numbers:
        # Check if the room exists
        room = db.query(models.Room).filter(models.Room.room_number == room_number).first()
        if not room:
            results.append({"room_number": room_number, "status": "error", "message": "Room does not exist."})
            continue

        # Check if there's an active reservation for this room
        reservation = db.query(models.Reservation).filter(
            models.Reservation.room_number == room_number,
            models.Reservation.status == "booked"
        ).first()

        if not reservation:
            results.append({"room_number": room_number, "status": "error", "message": "Room is not currently booked."})
            continue

        try:
            # Update reservation status
            reservation.status = "checked-out"
            db.commit()

            # Update room status
            room.status = "available"
            db.commit()

            results.append({"room_number": room_number, "status": "success", "message": f"Room {room_number} successfully checked out."})
        except Exception as e:
            db.rollback()
            results.append({"room_number": room_number, "status": "error", "message": str(e)})

    return {"results": results}



@app.delete("/reservations/{room_number}", tags=["Reservations"])
def delete_reservation_or_check_in(
    room_number: str,
    db: Session = Depends(get_db),
    current_user: UserDisplaySchema = Depends(get_current_user)
):
    """
    Delete a reservation or check-in for a room.
    1. Only admins can delete reservations or check-ins.
    2. Deletes the reservation or check-in record completely.
    3. Updates the room status to "available" after deletion.
    """

    # Ensure the user has admin permissions
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not have permission to delete reservations.")

    # Fetch the reservation by room number
    reservation = db.query(models.Reservation).filter(models.Reservation.room_number == room_number).first()

    if not reservation:
        raise HTTPException(status_code=404, detail="No reservation found for the specified room number.")

    try:
        # Fetch the room associated with the reservation
        room = db.query(models.Room).filter(models.Room.room_number == room_number).first()

        if not room:
            raise HTTPException(status_code=404, detail="Room not found for the specified room number.")

        # Delete the reservation or check-in record
        db.delete(reservation)

        # Update the room's status to "available"
        room.status = "available"

        # Commit the changes to the database
        db.commit()

        return {
            "message": f"Reservation or check-in for room {room_number} has been successfully deleted.",
            "room_status": room.status,
        }

    except SQLAlchemyError as e:
        db.rollback()  # Rollback the transaction in case of an error
        raise HTTPException(status_code=500, detail=f"An error occurred while deleting the reservation: {str(e)}")