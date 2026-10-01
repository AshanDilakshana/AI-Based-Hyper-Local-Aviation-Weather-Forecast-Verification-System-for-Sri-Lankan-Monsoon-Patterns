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

class UserDetailUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    organisation: Optional[str] = None
    station: Optional[str] = None

class UserPasswordReset(BaseModel):
    new_password: str

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

@router.put("/users/{id}")
def update_user_details(id: int, data: UserDetailUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        user.email = data.email
    if data.role is not None:
        user.role = data.role
    if data.organisation is not None:
        user.organisation = data.organisation
    if data.station is not None:
        user.station = data.station
    
    db.commit()
    
    log = SystemLogs(
        level="info",
        component="Admin_Users",
        message=f"User {user.username} details updated by admin."
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    user.hashed_password = "---"
    return user

@router.put("/users/{id}/password")
def reset_user_password(id: int, data: UserPasswordReset, db: Session = Depends(get_db)):
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    
    user.hashed_password = pwd_context.hash(data.new_password)
    db.commit()
    
    log = SystemLogs(
        level="info",
        component="Admin_Users",
        message=f"Password reset for user {user.username} by admin."
    )
    db.add(log)
    db.commit()
    return {"message": f"Password for {user.username} has been reset successfully."}

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
                
        # Drop rows where all required columns are completely empty (so we skip true blank rows)
        df = df.dropna(how='all')

        # Bulk insert
        new_flights = []
        for _, row in df.iterrows():
            f_val = str(row.get('flight', '')).strip()
            if f_val == 'nan':
                f_val = None
                
            dep_val = str(row.get('departuretime', '')).strip()
            if dep_val == 'nan':
                dep_val = None
                
            dest_val = str(row.get('destination', '')).strip().upper()
            if dest_val == 'NAN':
                dest_val = None

            new_flights.append(FlightTimeAndFlights(
                flight=f_val,
                departure_time_local=dep_val,
                destination=dest_val,
                time_period_mins=int(row['durationmins']) if pd.notna(row.get('durationmins')) else 0
            ))
            
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


# ── Route Alternatives ─────────────────────────────────────────────

from backend.data.models import RouteAlternatives

class RouteAltCreate(BaseModel):
    region_name: str
    airports: str  # Comma-separated ICAO codes

class RouteAltUpdate(BaseModel):
    region_name: Optional[str] = None
    airports: Optional[str] = None

@router.get("/routes")
def get_routes(db: Session = Depends(get_db)):
    return db.query(RouteAlternatives).order_by(RouteAlternatives.region_name).all()

@router.post("/routes")
def add_route(route: RouteAltCreate, db: Session = Depends(get_db)):
    existing = db.query(RouteAlternatives).filter(RouteAlternatives.region_name == route.region_name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Region '{route.region_name}' already exists.")
    new_route = RouteAlternatives(
        region_name=route.region_name,
        airports=route.airports
    )
    db.add(new_route)
    db.commit()
    db.refresh(new_route)
    
    log = SystemLogs(level="info", component="Admin_Routes", message=f"Route region '{route.region_name}' created.")
    db.add(log)
    db.commit()
    return new_route

@router.put("/routes/{id}")
def update_route(id: int, route: RouteAltUpdate, db: Session = Depends(get_db)):
    db_route = db.query(RouteAlternatives).filter(RouteAlternatives.id == id).first()
    if not db_route:
        raise HTTPException(status_code=404, detail="Route not found")
    if route.region_name is not None:
        db_route.region_name = route.region_name
    if route.airports is not None:
        db_route.airports = route.airports
    db.commit()
    db.refresh(db_route)
    
    log = SystemLogs(level="info", component="Admin_Routes", message=f"Route region '{db_route.region_name}' updated.")
    db.add(log)
    db.commit()
    return db_route

@router.delete("/routes/{id}")
def delete_route(id: int, db: Session = Depends(get_db)):
    db_route = db.query(RouteAlternatives).filter(RouteAlternatives.id == id).first()
    if not db_route:
        raise HTTPException(status_code=404, detail="Route not found")
    name = db_route.region_name
    db.delete(db_route)
    db.commit()
    
    log = SystemLogs(level="info", component="Admin_Routes", message=f"Route region '{name}' deleted.")
    db.add(log)
    db.commit()
    return {"message": f"Route '{name}' deleted successfully."}


# ── System Logs ────────────────────────────────────────────────────

@router.get("/logs")
def get_system_logs(db: Session = Depends(get_db)):
    return db.query(SystemLogs).order_by(SystemLogs.timestamp_utc.desc()).limit(500).all()

# ── Dashboard Stats ────────────────────────────────────────────────

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_flights = db.query(FlightTimeAndFlights).filter(FlightTimeAndFlights.flight != None).count()
    total_routes = db.query(RouteAlternatives).count()
    recent_logs = db.query(SystemLogs).order_by(SystemLogs.timestamp_utc.desc()).limit(5).all()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "total_flights": total_flights,
        "total_routes": total_routes,
        "recent_logs": recent_logs
    }

