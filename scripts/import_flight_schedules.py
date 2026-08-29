import os
import sys
import json
import pandas as pd
import math

# Add the project root to sys.path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.data.database import SessionLocal, engine, Base
from backend.data.models import FlightTimeAndFlights

# Create all tables (this will create the new table since we added it to models)
Base.metadata.create_all(bind=engine)

EXCEL_PATH = "/Users/Ashan/Research Project/frontend/Untitled/AI-Based-Hyper-Local-Aviation-Weather-Forecast-Verification-System-for-Sri-Lankan-Monsoon-Patterns/FLIGHT SHEDULE.xlsx"
JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "data", "historical_flight_data.json")

def parse_excel_time(val):
    if pd.isna(val):
        return 0
    
    # If it's a float like 9.40 -> 9 hours, 40 mins
    try:
        f_val = float(val)
        hours = math.floor(f_val)
        minutes = round((f_val - hours) * 100)
        return int(hours * 60 + minutes)
    except:
        return 0

def import_data():
    db = SessionLocal()
    
    # 1. Clear existing data to prevent duplicates on re-run
    db.query(FlightTimeAndFlights).delete()
    db.commit()
    
    records_added = 0
    
    # 2. Read and insert Excel Data
    if os.path.exists(EXCEL_PATH):
        print(f"Reading Excel: {EXCEL_PATH}")
        df = pd.read_excel(EXCEL_PATH)
        
        # Expected columns: ['FLIGHT', 'DEPARTURE TIME (LOCAL)', 'DESTINATION', 'TIME PERIOD ']
        for _, row in df.iterrows():
            flight = str(row.get('FLIGHT', ''))
            dep_time = str(row.get('DEPARTURE TIME (LOCAL)', ''))
            dest = str(row.get('DESTINATION', '')).strip()
            time_period = row.get('TIME PERIOD ')
            
            if not dest or str(dest) == 'nan':
                continue
                
            time_mins = parse_excel_time(time_period)
            
            new_record = FlightTimeAndFlights(
                flight=flight if flight and flight != 'nan' else None,
                departure_time_local=dep_time if dep_time and dep_time != 'nan' else None,
                destination=dest,
                time_period_mins=time_mins
            )
            db.add(new_record)
            records_added += 1
            
    # 3. Read and insert JSON Data
    if os.path.exists(JSON_PATH):
        print(f"Reading JSON: {JSON_PATH}")
        with open(JSON_PATH, 'r') as f:
            historical_data = json.load(f)
            
        for key, value in historical_data.items():
            # key could be "VCBI-WMKP" or "WMKP"
            dest = key.split('-')[-1] if '-' in key else key
            # value is [duration_mins, stops, name]
            duration = int(value[0])
            
            # Check if this destination already exists from Excel to avoid exact duplicates
            # (Though it's okay to have multiple, let's just insert all since Excel has flight numbers)
            new_record = FlightTimeAndFlights(
                flight=None,
                departure_time_local=None,
                destination=dest,
                time_period_mins=duration
            )
            db.add(new_record)
            records_added += 1
            
    db.commit()
    db.close()
    
    print(f"Successfully migrated {records_added} flight schedule records to the database.")

if __name__ == "__main__":
    import_data()
