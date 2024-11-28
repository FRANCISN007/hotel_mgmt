from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
#from auth import pwd_context, authenticate_user, create_access_token, get_current_user
from app.users.auth import pwd_context, authenticate_user, create_access_token, get_current_user

from app.database import get_db
from . import crud, schemas  # Import user-specific CRUD and schemas
from app.users import crud as user_crud  # Correct import for user CRUD operations
import os



router = APIRouter()

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')


@router.post("/register/")
def register_user(user: schemas.UserSchema, db: Session = Depends(get_db)):
    # Check if the username already exists
    existing_user = user_crud.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check admin registration
    if user.role == "admin":
        if not user.admin_password or user.admin_password != ADMIN_PASSWORD:
            raise HTTPException(status_code=403, detail="Invalid admin password")

    # Hash the password and create the user
    hashed_password = pwd_context.hash(user.password)
    user_crud.create_user(db, user, hashed_password)
    return {"message": "User registered successfully"}


@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}




@router.get("/users/", response_model=list[schemas.UserDisplaySchema])
def list_all_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10,
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    #if current_user.role != "admin":
        #raise HTTPException(status_code=403, detail="Insufficient permissions")

    users = user_crud.get_all_users(db)
    return users


@router.delete("/users/{username}")
def delete_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserDisplaySchema = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    user = user_crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": f"User {username} deleted successfully"}
