from sqlalchemy.orm import Session
from reservations import models, schemas
from rooms.models import Room

def create_reservation(db: Session, reservation: schemas.ReservationSchema):
    """Create a new reservation."""
    db_reservation = models.Reservation(
        room_number=reservation.room_number,
        guest_name=reservation.guest_name,
        arrival_date=reservation.arrival_date,
        departure_date=reservation.departure_date,
        status=reservation.status,
    )
    # Mark the room as reserved
    room = db.query(Room).filter(Room.room_number == reservation.room_number).first()
    if room:
        room.status = "reserved"
        db.commit()

    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation

def get_reservation_by_id(db: Session, reservation_id: int):
    """Fetch a reservation by its ID."""
    return db.query(models.Reservation).filter(models.Reservation.id == reservation_id).first()

def get_reservations_by_room_number(db: Session, room_number: str):
    """Fetch all reservations for a specific room."""
    return db.query(models.Reservation).filter(models.Reservation.room_number == room_number).all()

def get_all_reservations(db: Session, skip: int = 0, limit: int = 10):
    """Fetch all reservations with optional pagination."""
    return db.query(models.Reservation).offset(skip).limit(limit).all()

def update_reservation_status(db: Session, reservation_id: int, status: str):
    """Update the status of a reservation."""
    reservation = get_reservation_by_id(db, reservation_id)
    if reservation:
        reservation.status = status
        db.commit()
        db.refresh(reservation)
        return reservation
    return None

def delete_reservation(db: Session, room_number: str):
    """Delete a reservation and free up the associated room."""
    reservation = db.query(models.Reservation).filter(models.Reservation.room_number == room_number).first()
    if reservation:
        # Free up the room
        room = db.query(Room).filter(Room.room_number == room_number).first()
        if room:
            room.status = "available"
            db.commit()
        
        db.delete(reservation)
        db.commit()
        return True
    return False

def check_out_multiple_rooms(db: Session, room_numbers: list[str]):
    """Check out multiple rooms and free them up."""
    for room_number in room_numbers:
        reservation = db.query(models.Reservation).filter(models.Reservation.room_number == room_number).first()
        if reservation:
            db.delete(reservation)
            
            room = db.query(Room).filter(Room.room_number == room_number).first()
            if room:
                room.status = "available"
        
    db.commit()
    return {"message": f"Checked out rooms: {', '.join(room_numbers)}"}

def room_summary(db: Session):
    """Return a summary of room statuses."""
    summary = {
        "total_rooms": db.query(Room).count(),
        "available": db.query(Room).filter(Room.status == "available").count(),
        "reserved": db.query(Room).filter(Room.status == "reserved").count(),
        "checked-in": db.query(Room).filter(Room.status == "checked-in").count(),
        "maintenance": db.query(Room).filter(Room.status == "maintenance").count(),
    }
    return summary
