from fastapi import APIRouter, HTTPException, Depends
from fastapi import Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import date
from app.database import get_db
from typing import Optional  # Import for optional parameters
from app.users.auth import get_current_user
from sqlalchemy import or_
from sqlalchemy import and_
from app.rooms import models as room_models  # Import room models
from app.bookings import schemas, models as  booking_models
from app.payments import models as payment_models
from loguru import logger
from sqlalchemy.sql import func
from datetime import datetime


router = APIRouter()

# Set up logging
logger.add("app.log", rotation="500 MB", level="DEBUG")



@router.post("/create/")
def create_booking(
    booking_request: schemas.BookingSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    room_number_input = booking_request.room_number.strip()
    normalized_room_number = room_number_input.lower()
    today = date.today()

    # Validate dates
    if booking_request.departure_date < booking_request.arrival_date:
        raise HTTPException(
            status_code=400,
            detail="Departure date must be later than the arrival date.",
        )

    # Check if booking type is Complimentary
    if booking_request.booking_type == "complimentary":
        if booking_request.arrival_date != today:
            raise HTTPException(
                status_code=400,
                detail="complimentary bookings can only be made for today's date.",
            )
        
        # Validate room existence
        room = (
            db.query(room_models.Room)
            .filter(func.lower(room_models.Room.room_number) == normalized_room_number)
            .first()
        )
        if not room:
            raise HTTPException(status_code=404, detail=f"Room {room_number_input} not found.")

        # Check if the room is available
        overlapping_booking = db.query(booking_models.Booking).filter(
            func.lower(booking_models.Booking.room_number) == normalized_room_number,
            booking_models.Booking.status != "checked-out",
            booking_models.Booking.status != "cancelled",
            or_(
                and_(
                    booking_models.Booking.arrival_date < booking_request.departure_date,
                    booking_models.Booking.departure_date > booking_request.arrival_date,
                )
            )
        ).first()

        if overlapping_booking:
            raise HTTPException(
                status_code=400,
                detail=f"Room {room_number_input} is already booked for the requested dates.",
            )
        
        booking_cost = 0
        payment_status = "complimentary"
        booking_status = "checked-in"

    else:
        # Validate standard booking types
        if booking_request.booking_type == "checked-in":
            if booking_request.arrival_date != today:
                raise HTTPException(
                    status_code=400,
                    detail="Check-in bookings can only be made for today's date.",
                )
        elif booking_request.booking_type == "reservation":
            if booking_request.arrival_date <= today:
                raise HTTPException(
                    status_code=400,
                    detail="Reserved bookings must be for a future date. Use the check-in option for today's booking.",
                )
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid booking type. Use 'Checked-in', 'Reservation', or 'Com' for complimentary.",
            )

        room = (
            db.query(room_models.Room)
            .filter(func.lower(room_models.Room.room_number) == normalized_room_number)
            .first()
        )
        if not room:
            raise HTTPException(status_code=404, detail=f"Room {room_number_input} not found.")

        overlapping_booking = db.query(booking_models.Booking).filter(
            func.lower(booking_models.Booking.room_number) == normalized_room_number,
            booking_models.Booking.status != "checked-out",
            booking_models.Booking.status != "cancelled",
            or_(
                and_(
                    booking_models.Booking.arrival_date < booking_request.departure_date,
                    booking_models.Booking.departure_date > booking_request.arrival_date,
                )
            )
        ).first()

        if overlapping_booking:
            raise HTTPException(
                status_code=400,
                detail=f"Room {room_number_input} is already booked for the requested dates.",
            )
        
        booking_cost = room.amount * booking_request.number_of_days
        payment_status = "pending"
        booking_status = "reserved" if booking_request.booking_type == "reservation" else "checked-in"

    try:
        new_booking = booking_models.Booking(
            room_number=room.room_number,
            guest_name=booking_request.guest_name,
            arrival_date=booking_request.arrival_date,
            departure_date=booking_request.departure_date,
            booking_type=booking_request.booking_type,
            phone_number=booking_request.phone_number,
            status=booking_status,
            room_price=room.amount if booking_request.booking_type != "Com" else 0,
            booking_cost=booking_cost,
            payment_status=payment_status,
        )
        db.add(new_booking)

        room.status = booking_status
        db.commit()
        db.refresh(new_booking)

        return {
            "message": f"Booking created successfully for room {room.room_number}.",
            "booking_details": {
                "id": new_booking.id,
                "room_number": new_booking.room_number,
                "guest_name": new_booking.guest_name,
                "room_price": new_booking.room_price,
                "arrival_date": new_booking.arrival_date,
                "departure_date": new_booking.departure_date,
                "booking_type": new_booking.booking_type,
                "phone_number": new_booking.phone_number,
                "booking_date": new_booking.booking_date.isoformat(),
                "number_of_days": new_booking.number_of_days,
                "status": new_booking.status,
                "booking_cost": new_booking.booking_cost,
                "payment_status": new_booking.payment_status,
            },
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


   
    

@router.get("/list")
def list_bookings(
    start_date: Optional[date] = Query(None, description="date format-yyyy-mm-dd"),
    end_date: Optional[date] = Query(None, description="date format-yyyy-mm-dd"),
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    try:
        # Ensure that the start_date is not greater than end_date
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="Start date cannot be later than end date, check your date entry"
            )

        # Set the start and end dates to the beginning and end of the day, if provided
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None

        # Build the base query for bookings
        query = db.query(booking_models.Booking).filter(
            booking_models.Booking.status != "cancelled"  # Exclude cancelled bookings
        )

        if start_datetime:
            query = query.filter(booking_models.Booking.booking_date >= start_datetime)
        if end_datetime:
            query = query.filter(booking_models.Booking.booking_date <= end_datetime)

        # Retrieve the bookings sorted by booking_date in descending order
        bookings = query.order_by(booking_models.Booking.booking_date.desc()).all()

        # Calculate total booking cost (excluding cancelled bookings)
        total_booking_cost = sum(booking.booking_cost for booking in bookings)

        # Format bookings for response
        formatted_bookings = [
            {
                "id": booking.id,
                "room_number": booking.room_number,
                "guest_name": booking.guest_name,
                "arrival_date": booking.arrival_date,
                "departure_date": booking.departure_date,
                "number_of_days": booking.number_of_days,
                "booking_type": booking.booking_type,
                "phone_number": booking.phone_number,
                "booking_date": booking.booking_date,
                "status": booking.status,
                "payment_status": booking.payment_status,
                "booking_cost": booking.booking_cost,
            }
            for booking in bookings
        ]

        return {
            "total_bookings": len(formatted_bookings),
            "total_booking_cost": total_booking_cost,  # Excluding canceled bookings
            "bookings": formatted_bookings,
        }

    except Exception as e:
        logger.error(f"Error retrieving bookings by date: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f" {str(e)}",
        )



@router.get("/status")
def list_bookings_by_status(
    status: Optional[str] = Query(None, description="Booking status to filter by (checked-in, reserved, checked-out, cancelled, complimentary)"),
    start_date: Optional[date] = Query(None, description="Filter by booking date (start) in format yyyy-mm-dd"),
    end_date: Optional[date] = Query(None, description="Filter by booking date (end) in format yyyy-mm-dd"),
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    try:
        # Build the base query
        query = db.query(booking_models.Booking)

        # Special condition: If searching for "complimentary", filter by payment_status
        if status:
            if status.lower() == "complimentary":
                query = query.filter(booking_models.Booking.payment_status == "complimentary")
            else:
                query = query.filter(booking_models.Booking.status == status)

        # Apply date filters based on booking_date
        if start_date:
            query = query.filter(booking_models.Booking.booking_date >= start_date)
        if end_date:
            query = query.filter(booking_models.Booking.booking_date <= end_date)

        # Execute the query and get the results
        bookings = query.all()

        # If no bookings are found, return a message with no bookings found
        if not bookings:
            return {"message": "No bookings found for the given criteria."}

        # Format the bookings to include necessary details
        formatted_bookings = [
            {
                "id": booking.id,
                "room_number": booking.room_number,
                "guest_name": booking.guest_name,
                "arrival_date": booking.arrival_date,
                "departure_date": booking.departure_date,
                "number_of_days": booking.number_of_days,
                "phone_number": booking.phone_number,
                "booking_date": booking.booking_date,  # Booking Date as the filter
                "status": booking.status,
                "booking_type": booking.booking_type,
                "payment_status": booking.payment_status,  # Includes payment status
                "booking_cost": booking.booking_cost,
            }
            for booking in bookings
        ]

        # Return the formatted response
        return {
            "total_bookings": len(formatted_bookings),
            "bookings": formatted_bookings if formatted_bookings else []  # Ensure bookings is always a list
        }

    except Exception as e:
        logger.error(f"Error retrieving bookings by status and booking date: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}",
        )




@router.get("/search")
def search_guest_name(
    guest_name: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Search for bookings by guest name.
    Returns all bookings matching the given guest name.
    """
    try:
        bookings = db.query(booking_models.Booking).filter(
            booking_models.Booking.guest_name.ilike(f"%{guest_name}%"),
            
        ).all()


        if not bookings:
            raise HTTPException(status_code=404, detail=f"No bookings found for guest '{guest_name}'.")

        formatted_bookings = []
        for booking in bookings:
            formatted_bookings.append({
                "id": booking.id,
                "room_number": booking.room_number,
                "guest_name": booking.guest_name,
                "arrival_date": booking.arrival_date,
                "departure_date": booking.departure_date,
                "number_of_days": booking.number_of_days,
                "booking_type": booking.booking_type,
                "phone_number": booking.phone_number,
                "booking_date":booking.booking_date,
                "status": booking.status,
                "payment_status": booking.payment_status,
                "booking_cost":booking.booking_cost,
            })

        return {
            "total_bookings": len(formatted_bookings),
            "bookings": formatted_bookings,
        }

    except Exception as e:
        logger.error(f"Error searching bookings for guest '{guest_name}': {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f" {str(e)}",
        )



@router.get("/{booking_id}")
def list_booking_by_id(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    
    # Fetch the booking by ID
    booking = db.query(booking_models.Booking).filter(
        booking_models.Booking.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found.")

    # Format the response
    formatted_booking = {
        "id": booking.id,
        "room_number": booking.room_number,
        "guest_name": booking.guest_name,
        "arrival_date": booking.arrival_date,
        "departure_date": booking.departure_date,
        "number_of_days": booking.number_of_days,
        "booking_type": booking.booking_type,
        "phone_number": booking.phone_number,
        "booking_date": booking.booking_date,
        "status": booking.status,
        "payment_status": booking.payment_status,
        "booking_cost": booking.booking_cost,
    }

    return {"message": f"Booking details for ID {booking_id} retrieved successfully.", "booking": formatted_booking}


@router.get("/room/{room_number}")
def list_bookings_by_room(
    room_number: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    List all bookings associated with a specific room number within an optional date range.
    """
    try:
        # Normalize room_number to lowercase
        normalized_room_number = room_number.lower()

        # Check if the room exists in the database (case-insensitive)
        room_exists = db.query(room_models.Room).filter(
            func.lower(room_models.Room.room_number) == normalized_room_number
        ).first()

        if not room_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Room number {room_number} does not exist.",
            )

        # Build the base query for bookings (case-insensitive)
        bookings_query = db.query(booking_models.Booking).filter(
            func.lower(booking_models.Booking.room_number) == normalized_room_number
        )

        # Apply date range filters based on booking_date
        if start_date:
            bookings_query = bookings_query.filter(booking_models.Booking.booking_date >= start_date)
        if end_date:
            bookings_query = bookings_query.filter(booking_models.Booking.booking_date <= end_date)

        # Fetch bookings
        bookings = bookings_query.all()

        if not bookings:
            raise HTTPException(
                status_code=404,
                detail=f"No bookings found for room number {room_number}.",
            )

        # Format the bookings for response
        formatted_bookings = [
            {
                "id": booking.id,
                "room_number": booking.room_number,
                "guest_name": booking.guest_name,
                "arrival_date": booking.arrival_date,
                "departure_date": booking.departure_date,
                "number_of_days": booking.number_of_days,
                "booking_type": booking.booking_type,
                "phone_number": booking.phone_number,
                "booking_date": booking.booking_date,
                "status": booking.status,
                "payment_status": booking.payment_status,
                "booking_cost": booking.booking_cost,
            }
            for booking in bookings
        ]

        return {
            "room_number": normalized_room_number,
            "total_bookings": len(formatted_bookings),
            "bookings": formatted_bookings,
        }
    except Exception as e:
        logger.error(f"Error retrieving bookings for room {room_number}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"{str(e)}"
        )



@router.put("/update/")
def update_booking(
    booking_id: int,
    updated_data: schemas.BookingSchema,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    """
    Update booking details (reservation or check-in) by booking ID.
    """
    try:
        booking = db.query(booking_models.Booking).filter(booking_models.Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found.")

        room = None  # Variable to store the room instance

        # Step 1: Handle Room Number Update
        if updated_data.room_number:
            room_number_input = updated_data.room_number.strip()
            normalized_room_number = room_number_input.lower()

            # Fetch the new room
            room = (
                db.query(room_models.Room)
                .filter(func.lower(room_models.Room.room_number) == normalized_room_number)
                .first()
            )
            if not room:
                raise HTTPException(status_code=404, detail=f"Room {room_number_input} not found.")

            # Check for conflicting bookings
            overlapping_booking = db.query(booking_models.Booking).filter(
                func.lower(booking_models.Booking.room_number) == normalized_room_number,
                booking_models.Booking.id != booking_id,  # Exclude the current booking
                booking_models.Booking.status.notin_(["checked-out", "cancelled"]),
                or_(
                    and_(
                        booking_models.Booking.arrival_date < updated_data.departure_date,
                        booking_models.Booking.departure_date > updated_data.arrival_date,
                    )
                ),
            ).first()

            if overlapping_booking:
                raise HTTPException(
                    status_code=400,
                    detail=f"Room {room_number_input} is already booked for the requested dates.",
                )

            # Update room number with correct case
            updated_data.room_number = room.room_number

        # Step 2: Fetch Existing Room if Room Number is NOT Changed
        if not room:
            room = db.query(room_models.Room).filter(room_models.Room.room_number == booking.room_number).first()
            if not room:
                raise HTTPException(status_code=404, detail=f"Room {booking.room_number} not found.")

        # Step 3: Ensure Number of Days is Valid
        number_of_days = updated_data.number_of_days if updated_data.number_of_days is not None else booking.number_of_days
        if number_of_days is None or number_of_days <= 0:
            raise HTTPException(status_code=400, detail="Number of days must be greater than zero.")

        # Step 4: Calculate Booking Cost
        booking_cost = number_of_days * room.amount

        # Step 5: Update Booking Fields
        for field, value in updated_data.dict(exclude_unset=True).items():
            setattr(booking, field, value)

        # Ensure Booking Cost is Updated
        booking.booking_cost = booking_cost

        db.commit()
        db.refresh(booking)

        # Step 6: Serialize Response
        serialized_booking = schemas.BookingSchemaResponse.from_orm(booking)

        return {
            "message": "Booking updated successfully.",
            "updated_booking": serialized_booking.dict()
        }

    except Exception as e:
        db.rollback()
        print(f"Error updating booking: {str(e)}")  # Debugging Output
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    
  
@router.put("/{room_number}/")
def guest_checkout(
    room_number: str,  # Room number is now passed as a string
    db: Session = Depends(get_db),
):
    """
    Endpoint to check out a guest by room number.
    Updates the booking status to 'checked-out' and the room status to 'available'.
    """
    try:
        # Step 1: Retrieve the booking by room number and ensure it is 'checked-in' or 'reserved'
        booking = db.query(booking_models.Booking).filter(
            func.lower(booking_models.Booking.room_number) == room_number.lower(),  # Case-insensitive comparison
            booking_models.Booking.status.in_(["checked-in", "reserved"])  # Allow both statuses
        ).first()

        if not booking:
            raise HTTPException(
                status_code=404,
                detail=f"Ths room number {room_number} is not booked yet, so it's not in a valid state for checkout."
            )

        # Step 2: Retrieve the associated room with case-insensitive comparison
        room = db.query(room_models.Room).filter(
            func.lower(room_models.Room.room_number) == room_number.lower()  # Match the room number case-insensitively
        ).first()

        if not room:
            raise HTTPException(
                status_code=404,
                detail=f"Room number {room_number} not found."
            )

        # Step 3: Update booking and room statuses
        booking.status = "checked-out"
        room.status = "available"

        # Commit the changes to the database
        db.commit()

        return {
            "message": f"Guest checked out successfully for room number {room_number}.",
            "room_status": room.status,
            "booking_status": booking.status,
        }

    except HTTPException as e:
        # Re-raise the HTTP exception
        raise e
    except Exception as e:
        # Handle unexpected errors
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during checkout: {str(e)}"
        )


   
    
@router.post("/cancel/{booking_id}/")
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    """
    Cancel a booking if no non-voided payment is tied to it. If a payment exists, raise an exception.
    """
    # Fetch the booking by ID
    booking = db.query(booking_models.Booking).filter(
        booking_models.Booking.id == booking_id, booking_models.Booking.deleted == False
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail=f"Booking with ID {booking_id} not found or already canceled."
        )

    # Check if the booking has any associated payments
    payment = db.query(payment_models.Payment).filter(
        payment_models.Payment.booking_id == booking_id
    ).first()

    # If payment exists and is not voided, raise an exception
    if payment and payment.status != "voided":
        raise HTTPException(
            status_code=400,
            detail="Booking is tied to a non-voided payment. Please cancel or delete the payment before canceling the booking."
        )

    # Proceed with cancellation if no valid payment exists or all payments are voided
    try:
        # Update the booking status to 'cancelled'
        booking.status = "cancelled"
        booking.deleted = True  # Mark as soft deleted, indicating cancellation

        # Update the room status to 'available'
        room = db.query(room_models.Room).filter(
            room_models.Room.room_number == booking.room_number
        ).first()
        if room:
            room.status = "available"

        db.commit()
        return {
            "message": f"Booking ID {booking_id} has been canceled successfully.",
            "canceled_booking": {
                "id": booking.id,
                "room_number": booking.room_number,
                "guest_name": booking.guest_name,
                "status": booking.status,  # Showing the updated status as 'cancelled'
                "room_status": room.status if room else "N/A",  # Showing the updated room status
            },
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while canceling the booking: {str(e)}"
        )



