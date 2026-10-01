from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from backend.data.database import get_db
from backend.data.models import FlightTimeAndFlights, SystemLogs, User
import pandas as pd
import io
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/admin", tags=["admin"])

class UserStatusUpdate(BaseModel):
    is_active: bool

class FlightScheduleCreate(BaseModel):
    flight: str
    departure_time_local: str
    destination: str
    time_period_mins: int

class FlightScheduleUpdate(BaseModel):
    flight: Optional[str] = None
    departure_time_local: Optional[str] = None
    destination: Optional[str] = None
    time_period_mins: Optional[int] = None

@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    # Mask passwords
    for user in users:
        user.hashed_password = "---"
    return users

@router.put("/users/{id}/status")
def update_user_status(id: int, status: UserStatusUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = status.is_active
    db.commit()
    
    log = SystemLogs(
        level="info",
        component="Admin_Users",
        message=f"User {user.username} {'activated' if status.is_active else 'deactivated'}."
    )
    db.add(log)
    db.commit()
    return {"message": "Status updated successfully", "is_active": user.is_active}

@router.get("/flights")
def get_flights(db: Session = Depends(get_db)):
    return db.query(FlightTimeAndFlights).order_by(FlightTimeAndFlights.id.desc()).all()

@router.post("/flights")
def add_flight(flight: FlightScheduleCreate, db: Session = Depends(get_db)):
    new_flight = FlightTimeAndFlights(
        flight=flight.flight,
        departure_time_local=flight.departure_time_local,
        destination=flight.destination.upper(),
        time_period_mins=flight.time_period_mins
    )
    db.add(new_flight)
    db.commit()
    db.refresh(new_flight)
    return new_flight

@router.put("/flights/{id}")
def update_flight(id: int, flight: FlightScheduleUpdate, db: Session = Depends(get_db)):
    db_flight = db.query(FlightTimeAndFlights).filter(FlightTimeAndFlights.id == id).first()
    if not db_flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    if flight.flight is not None:
        db_flight.flight = flight.flight
    if flight.departure_time_local is not None:
        db_flight.departure_time_local = flight.departure_time_local
    if flight.destination is not None:
        db_flight.destination = flight.destination.upper()
    if flight.time_period_mins is not None:
        db_flight.time_period_mins = flight.time_period_mins
        
    db.commit()
    db.refresh(db_flight)
    return db_flight

@router.delete("/flights/{id}")
def delete_flight(id: int, db: Session = Depends(get_db)):
    db_flight = db.query(FlightTimeAndFlights).filter(FlightTimeAndFlights.id == id).first()
    if not db_flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    db.delete(db_flight)
    db.commit()
    return {"message": "Flight deleted successfully"}

@router.post("/flights/bulk-upload")
async def bulk_upload_flights(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV or Excel file.")
    
    try:
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
            
        # Standardize columns to lowercase and remove spaces
        df.columns = [c.strip().lower().replace(" ", "").replace("_", "") for c in df.columns]
        
        required_cols = ['flight', 'departuretime', 'destination', 'durationmins']
        
        # Check if all required columns are present (allow flexibility like 'departure time' which becomes 'departuretime')
        for col in required_cols:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Missing required column in file: '{col}'. Ensure your file has columns for Flight, Departure Time, Destination, and Duration Mins.")
                
        # Bulk insert
        new_flights = []
        for _, row in df.iterrows():
            f = FlightTimeAndFlights(
                flight=str(row['flight']),
                departure_time_local=str(row['departuretime']),
                destination=str(row['destination']).upper(),
                time_period_mins=int(row['durationmins'])
            )
            new_flights.append(f)
            
        db.bulk_save_objects(new_flights)
        db.commit()
        
        # Log this action
        log = SystemLogs(
            level="info",
            component="Admin_BulkUpload",
            message=f"Successfully imported {len(new_flights)} flights via bulk upload."
        )
        db.add(log)
        db.commit()
        
        return {"message": f"Successfully imported {len(new_flights)} flights."}
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
