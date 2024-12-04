from sqlalchemy.orm import Session
from app.reservations import models, schemas
from app.rooms.models import Room
from app.reservations import models as reservation_models
from sqlalchemy import and_
from app.check_in_guest import models as check_in_guest_models

def check_overlapping_check_in(
    db: Session, 
    room_number: str, 
    arrival_date, 
    departure_date
):
    """
    Checks if a given room has overlapping active check-ins within the specified date range.
    """
    overlapping_check_in = db.query(check_in_guest_models.Check_in).filter(
        check_in_guest_models.Check_in.room_number == room_number,
        and_(
            check_in_guest_models.Check_in.arrival_date <= departure_date,
            check_in_guest_models.Check_in.departure_date >= arrival_date
        ),
        check_in_guest_models.Check_in.status.in_(["reserved", "checked-in"])
        #reservation_models.Reservation.status == "checked_in"
    ).first()
    return overlapping_check_in



def check_overlapping_reservations(db: Session, room_number: str, arrival_date, departure_date):
    """
    Checks if a given room has overlapping reservations or is currently checked in within the specified date range.
    """
    overlapping_reservation = db.query(reservation_models.Reservation).filter(
        reservation_models.Reservation.room_number == room_number,
        and_(
            reservation_models.Reservation.arrival_date <= departure_date,
            reservation_models.Reservation.departure_date >= arrival_date
        ),
        reservation_models.Reservation.status.in_(["reserved", "checked_in"])
    ).first()
    return overlapping_reservation




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
