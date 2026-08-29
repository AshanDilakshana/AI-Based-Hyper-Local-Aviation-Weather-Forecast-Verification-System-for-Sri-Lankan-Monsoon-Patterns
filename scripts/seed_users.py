import sys
import os

# Ensure backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

from backend.data.database import SessionLocal
from backend.data.models import User
from backend.api.routers.auth_router import get_password_hash

db = SessionLocal()

forecaster = db.query(User).filter(User.username == "MET-04821").first()
if not forecaster:
    forecaster = User(
        username="MET-04821",
        hashed_password=get_password_hash("password123"),
        role="forecaster",
        name="A. Ranasinghe",
        email="officer@meteo.gov.lk",
        organisation="Department of Meteorology",
        station="VCBI · Bandaranaike Intl."
    )
    db.add(forecaster)

pilot = db.query(User).filter(User.username == "ATPL-SL-2291").first()
if not pilot:
    pilot = User(
        username="ATPL-SL-2291",
        hashed_password=get_password_hash("password123"),
        role="pilot",
        name="Capt. N. Fernando",
        email="crew@operator.lk",
        organisation="SriLankan Airlines",
        station="VCBI · Bandaranaike Intl."
    )
    db.add(pilot)

db.commit()
print("Seed completed.")
