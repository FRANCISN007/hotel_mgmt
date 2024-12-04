#main file
from fastapi import FastAPI
from app.database import engine, Base
from app.users.router import router as user_router
from app.rooms.router import router as rooms_router
from app.reservations.router import router as reservations_router
from app.check_in_guest.router import router as check_in_guest_router


app = FastAPI(
    title="Hotel Management System",
    description="An API for managing hotel operations including guests, reservations, and rooms.",
    version="1.0.0",
)


# Database initialization
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Include the user router
app.include_router(user_router, prefix="/user", tags=["Users"])
app.include_router(rooms_router, prefix="/rooms", tags=["Rooms"])
app.include_router(check_in_guest_router, prefix="/guest", tags=["Check-ins"])
app.include_router(reservations_router, prefix="/reservations", tags=["Reservations"])
