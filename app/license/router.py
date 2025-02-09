from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.users.auth import get_current_user
from app.license import schemas, services
from app.users import schemas
from app.license import schemas as license_schemas

import os

router = APIRouter()

# Hardcoded admin password (better to store in an environment variable)
ADMIN_LICENSE_PASSWORD = os.getenv("ADMIN_LICENSE_PASSWORD")

# Endpoint to generate a new license key (Admin Only)
@router.post("/generate", response_model=license_schemas.LicenseResponse)
def generate_license_key(license_password: str, key: str, db: Session = Depends(get_db)):
    
    if license_password != ADMIN_LICENSE_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid license password.")
    
    new_license = services.create_license_key(db, key)
    return new_license

# Endpoint to verify a license key
@router.get("/verify/{key}")
def verify_license(key: str, db: Session = Depends(get_db)):
    
    result = services.verify_license_key(db, key)
    
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result
