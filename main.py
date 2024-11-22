from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi import Request
from auth import pwd_context, authenticate_user, create_access_token, get_current_user
import auth, crud, schemas, models
from database import get_db
#from models import Base, engine
from database import engine, Base, get_db
#from logger import get_logger


#logger = get_logger(__name__)

app = FastAPI()

# Database initialization
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.post("/register/", tags= ["User"])
def register_user(user: schemas.UserSchema, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

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



@app.get("/rooms/booked", tags=["Rooms"])
def list_booked_rooms(
    db: Session = Depends(get_db)
):
    # Query rooms with status "booked"
    booked_rooms = db.query(models.Room).filter(models.Room.status == "booked").all()
    
    # Count the number of booked rooms
    total_booked_rooms = len(booked_rooms)
    
    # Check if there are any booked rooms
    if total_booked_rooms == 0:
        return {"message": "No rooms are currently booked."}
    
    # Return the list of booked rooms and the total count
    return {
        "booked_rooms": booked_rooms,
        "Total rooms booked": total_booked_rooms
    }

    # Create the room
    #new_room = crud.create_room(db, room)
    #return {"message": "Room created successfully", "room": new_room}


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

@app.get("/rooms/summary", tags=["Rooms"])
def room_summary(db: Session = Depends(get_db), current_user: schemas.UserDisplaySchema = Depends(get_current_user)):
    # Query total rooms
    total_rooms = db.query(models.Room).count()
    
    # Query booked rooms
    total_booked_rooms = db.query(models.Room).filter(models.Room.status == "booked").count()
    
    # Query available rooms
    total_available_rooms = db.query(models.Room).filter(models.Room.status == "available").count()
    
    # Determine message based on availability
    message = "Fully booked!" if total_available_rooms == 0 else f"{total_available_rooms} room(s) available."
    
    # Return summary
    return {
        "total_rooms": total_rooms,
        "rooms_booked": total_booked_rooms,
        "rooms_available": total_available_rooms,
        "message": message
    }



@app.post("/reservations/", tags=["Reservations"])
def create_reservation(reservation: schemas.ReservationSchema, db: Session = Depends(get_db)):
    # Ensure all required fields are provided
    if not reservation.room_number or not reservation.guest_name:
        raise HTTPException(status_code=400, detail="Room number and guest name are required.")

    # Check if the room exists by room_number
    room = db.query(models.Room).filter(models.Room.room_number == reservation.room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Check if the room is available
    if room.status != "available":
        raise HTTPException(status_code=400, detail="Room is not available for reservation")

    try:
        # Create the reservation
        new_reservation = models.Reservation(
            room_number=reservation.room_number,  # Use room_number from schema
            guest_name=reservation.guest_name,
            arrival_date=reservation.arrival_date,
            departure_date=reservation.departure_date,
            status="booked",
        )
        db.add(new_reservation)
        db.commit()
        db.refresh(new_reservation)

        # Update room status
        room.status = "booked"
        db.commit()

        return {"message": "Reservation created successfully", "reservation_id": new_reservation.id}
    except Exception as e:
        db.rollback()  # Roll back in case of error
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/reservations/", response_model=list[schemas.ReservationSchema], tags=["Reservations"])
def list_all_reservations(db: Session = Depends(get_db), current_user: schemas.UserDisplaySchema = Depends(get_current_user)):
    # Fetch all reservations from the database
    reservations = db.query(models.Reservation).all()
    
    # If no reservations exist, return an empty list
    if not reservations:
        raise HTTPException(status_code=404, detail="No reservations found")
    
    return reservations

@app.post("/reservations/check-in/", tags=["Reservations"])
def check_in_guest(
    check_in_request: schemas.CheckInSchema,  # Full details about the guest and room
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user)
):
    room_number = check_in_request.room_number

    # Check if the room exists
    room = db.query(models.Room).filter(models.Room.room_number == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

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
        db.commit()
        db.refresh(new_reservation)

        # Update the room status to "booked"
        room.status = "booked"
        db.commit()

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

@app.put("/reservations/check-out/{room_number}", tags=["Reservations"])
def check_out_guest(
    room_number: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user)
):
    # Check if the room exists
    room = db.query(models.Room).filter(models.Room.room_number == room_number).first()
    if not room:
        raise HTTPException(
            status_code=404,
            detail=f"Room with room number {room_number} does not exist."
        )

    # Check if there's an active reservation (checked-in status) for this room
    reservation = db.query(models.Reservation).filter(
        models.Reservation.room_number == room_number,
        models.Reservation.status == "booked"  # Ensure the reservation is for a checked-in guest
    ).first()

    if not reservation:
        raise HTTPException(
            status_code=400,
            detail=f"Room {room_number} is not booked, it's still available."
        )

    try:
        # Update the reservation status to "checked-out"
        reservation.status = "checked-out"
        db.commit()

        # Update the room status to "available"
        room.status = "available"
        db.commit()

        return {
            "message": f"Guest {reservation.guest_name} successfully checked out of room {room_number}",
            "reservation": {
                "guest_name": reservation.guest_name,
                "room_number": reservation.room_number,
                "arrival_date": reservation.arrival_date,
                "departure_date": reservation.departure_date,
                "status": reservation.status
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")



@app.delete("/reservations/{room_number}", tags=["Reservations"])
def cancel_reservation(
    room_number: str, 
    db: Session = Depends(get_db), 
    current_user: schemas.UserDisplaySchema = Depends(get_current_user)  # Ensure the user is authenticated
):
    # Check if the current user is an admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not have permission to delete reservations")

    # Fetch the reservation by room number
    reservation = db.query(models.Reservation).filter(models.Reservation.room_number == room_number).first()
    
    # If the reservation does not exist, raise a 404 error
    if not reservation:
        raise HTTPException(status_code=404, detail="No reservation found for the specified room number")
    
    try:
        # Fetch the associated room
        room = db.query(models.Room).filter(models.Room.room_number == room_number).first()
        
        # Update the room status to "available"
        if room and room.status == "booked":
            room.status = "available"
            db.commit()
        
        # Delete the reservation
        db.delete(reservation)
        db.commit()

        return {"message": f"Reservation for room number {room_number} has been cancelled successfully"}
    except Exception as e:
        db.rollback()  # Roll back in case of error
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

