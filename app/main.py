from fastapi import FastAPI
from app.database import engine, Base
from app.users.router import router as user_router
from app.rooms.router import router as rooms_router
from app.reservations.router import router as reservations_router
from app.bookings.router import router as bookings_router
from app.payments.router import router as payments_router  # Import the payments router
from loguru import logger


app = FastAPI(
    title="Hotel Management System",
    description="An API for managing hotel operations including guests, reservations, rooms, and payments.",
    version="1.0.0",
)

# Set up logging
logger.add("app.log", rotation="500 MB", level="DEBUG")

# Database initialization
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)  # Create all tables in the database
    

app.include_router(user_router, prefix="/user", tags=["Users"])
app.include_router(rooms_router, prefix="/rooms", tags=["Rooms"])
app.include_router(bookings_router, prefix="/guest", tags=["Bookings"])
app.include_router(reservations_router, prefix="/reservations", tags=["Reservations"])
app.include_router(payments_router, prefix="/payments", tags=["Payments"])  # Include the new payments routes
