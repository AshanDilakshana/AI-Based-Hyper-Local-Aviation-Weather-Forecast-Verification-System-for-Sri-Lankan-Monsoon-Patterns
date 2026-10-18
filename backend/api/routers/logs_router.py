from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from backend.data.database import get_db
from backend.data.models import SystemLogs

router = APIRouter(
    prefix="/logs",
    tags=["System & Activity Logs API"],
)


class LogCreate(BaseModel):
    level: str = "INFO"  # INFO, SUCCESS, WARNING, ERROR
    component: str
    message: str
    details: Optional[str] = None


# Sample seed logs if DB is empty
SEED_LOGS = [
    {
        "level": "SUCCESS",
        "component": "Live_METAR_Fetcher",
        "message": "Synchronized latest METAR data from BIA/CMB weather station.",
        "details": "Added 1 new observation record",
    },
    {
        "level": "INFO",
        "component": "MLOps_Retrainer",
        "message": "Evaluated 3H XGBoost Wind prediction model against current observations.",
        "details": "MAE: 1.42 kts, Status: Operational",
    },
    {
        "level": "SUCCESS",
        "component": "Forecast_Verification",
        "message": "Forecaster verified and published 3H forecast guidance.",
        "details": "Target: 1800Z, Wind: 14kts / 240°",
    },
    {
        "level": "INFO",
        "component": "Pilot_Briefing",
        "message": "Flight AL-502 pilot requested ICAO pre-flight briefing.",
        "details": "Route: CMB -> SIN, Flight Level: FL320",
    },
    {
        "level": "SUCCESS",
        "component": "Pilot_FlightPlan",
        "message": "Generated weather corridor briefing for Colombo (VCBI) to Male (VRMM).",
        "details": "Flight UL-101, Aircraft: A320neo",
    },
    {
        "level": "INFO",
        "component": "System",
        "message": "BIA Met data stream connected cleanly.",
        "details": "Interval: 30 minutes",
    },
    {
        "level": "WARNING",
        "component": "MLOps_Retrainer",
        "message": "Minor wind shear gradient detected near RWY 04 approach.",
        "details": "Crosswind component peak: 12 kts",
    },
    {
        "level": "INFO",
        "component": "Pilot_Document",
        "message": "Weather Briefing Package PDF downloaded by flight crew.",
        "details": "Document ID: WBP-2026-0812",
    },
]


def ensure_seed_logs(db: Session):
    try:
        pilot_count = (
            db.query(SystemLogs).filter(SystemLogs.component.ilike("Pilot_%")).count()
        )
        if pilot_count == 0:
            for seed in SEED_LOGS:
                log = SystemLogs(
                    timestamp_utc=datetime.utcnow(),
                    level=seed["level"],
                    component=seed["component"],
                    message=seed["message"],
                    details=seed["details"],
                )
                db.add(log)
            db.commit()
    except Exception as e:
        db.rollback()
        print("Error seeding logs:", e)


@router.get("")
@router.get("/")
def get_system_logs(
    role: str = Query(
        "forecaster", description="Role of requesting user: forecaster or pilot"
    ),
    level: Optional[str] = Query(None, description="Filter by log level"),
    limit: int = Query(50, description="Max logs to return"),
    db: Session = Depends(get_db),
):
    ensure_seed_logs(db)

    query = db.query(SystemLogs)

    # Role-based filtering
    if role.lower() == "pilot":
        # Pilots see only pilot-relevant logs
        query = query.filter(
            (SystemLogs.component.ilike("Pilot_%"))
            | (SystemLogs.component.ilike("Flight_%"))
            | (SystemLogs.component.ilike("Briefing%"))
            | (SystemLogs.component.ilike("Forecast_Verification%"))
        )
    # Forecasters see ALL logs without filter restriction

    if level and level.upper() != "ALL":
        query = query.filter(SystemLogs.level == level.upper())

    records = query.order_by(SystemLogs.timestamp_utc.desc()).limit(limit).all()

    result = []
    for r in records:
        result.append(
            {
                "id": r.id,
                "timestamp_utc": (
                    r.timestamp_utc.isoformat()
                    if r.timestamp_utc
                    else str(datetime.utcnow())
                ),
                "level": r.level,
                "component": r.component,
                "message": r.message,
                "details": r.details,
            }
        )
    return result


@router.post("")
@router.post("/")
def create_log(log_data: LogCreate, db: Session = Depends(get_db)):
    try:
        new_log = SystemLogs(
            timestamp_utc=datetime.utcnow(),
            level=log_data.level.upper(),
            component=log_data.component,
            message=log_data.message,
            details=log_data.details,
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return {"message": "Log entry created", "id": new_log.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to record log: {str(e)}")
