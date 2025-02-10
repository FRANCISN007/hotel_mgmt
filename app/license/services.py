from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.license.models import LicenseKey

# Generate a new license key with a 1-year expiration
def create_license_key(db: Session, key: str):
    expiration = datetime.utcnow() + timedelta(days=1)  # 1 year validity
    license_key = LicenseKey(key=key, expiration_date=expiration, is_active=True)
    db.add(license_key)
    db.commit()
    db.refresh(license_key)
    return license_key

# Validate an existing license key
def verify_license_key(db: Session, key: str):
    license_entry = db.query(LicenseKey).filter(LicenseKey.key == key, LicenseKey.is_active == True).first()

    if not license_entry:
        return {"valid": False, "message": "Invalid or inactive license key"}

    if license_entry.expiration_date < datetime.utcnow():
        license_entry.is_active = False
        db.commit()
        return {"valid": False, "message": "License expired"}

    return {"valid": True, "expires_on": license_entry.expiration_date}
