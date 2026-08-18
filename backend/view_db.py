import sqlite3
import os

def view_database():
    # Resolve the path to weather_system.db
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(backend_dir, "weather_data.db")
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return

    print("=" * 60)
    print(f"Connecting to SQLite Database: {db_path}")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. List Tables and Counts
    tables = ["observations", "predictions", "briefing_packages"]
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            count = cursor.fetchone()["cnt"]
            print(f"Table: {table:<20} | Total Records: {count}")
        except sqlite3.OperationalError:
            print(f"Table: {table:<20} | Status: Does not exist yet")
            
    # 2. Show recent observations
    print("\n" + "-" * 60)
    print("LATEST 3 WEATHER OBSERVATIONS (observations table):")
    print("-" * 60)
    try:
        cursor.execute("SELECT * FROM observations ORDER BY id DESC LIMIT 3")
        rows = cursor.fetchall()
        for r in rows:
            print(f"ID: {r['id']} | Time: {r['report_time']} | Temp: {r['temperature']}°C | Pressure: {r['pressure']} hPa | Wind: {r['wind_speed']} kt ({r['wind_direction']}°)")
    except Exception as e:
        print(f"Could not read observations: {e}")

    # 3. Show recent predictions
    print("\n" + "-" * 60)
    print("LATEST 3 MODEL FORECASTS (predictions table):")
    print("-" * 60)
    try:
        cursor.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT 3")
        rows = cursor.fetchall()
        for r in rows:
            verify_str = f"Verified (Temp Error: {r['temp_error']}°C, Status: {r['temp_status']})" if r['is_verified'] else "Pending Verification"
            print(f"ID: {r['id']} | Input Obs Time: {r['input_obs_time']} | Target Forecast Time: {r['forecast_time']} | Predicted Temp: {r['predicted_temperature']}°C | Predicted Pressure: {r['predicted_pressure']} hPa | Status: {verify_str}")
    except Exception as e:
        print(f"Could not read predictions: {e}")

    # 4. Show recent briefings
    print("\n" + "-" * 60)
    print("LATEST 3 PILOT BRIEFING PACKS (briefing_packages table):")
    print("-" * 60)
    try:
        cursor.execute("SELECT * FROM briefing_packages ORDER BY id DESC LIMIT 3")
        rows = cursor.fetchall()
        for r in rows:
            print(f"ID: {r['id']} | Requested: {r['request_time']} | Airport: {r['airport_code']} | FL: {r['flight_level']} | Region: Area {r['area']} | Chart Local Path: {r['chart_file_path']}")
    except Exception as e:
        print(f"Could not read briefings: {e}")

    print("=" * 60)
    conn.close()

if __name__ == "__main__":
    view_database()
