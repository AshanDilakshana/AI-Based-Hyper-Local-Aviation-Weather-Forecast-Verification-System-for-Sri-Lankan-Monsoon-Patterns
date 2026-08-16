import sqlite3
import os

def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Create observations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            obs_time INTEGER UNIQUE,          -- Unix timestamp in seconds
            report_time TEXT NOT NULL,         -- ISO timestamp string (e.g. "2026-08-07T15:10:00Z")
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            pressure REAL NOT NULL,
            dew_point REAL NOT NULL,
            wind_speed REAL NOT NULL,
            wind_direction REAL NOT NULL,
            visibility REAL NOT NULL,
            raw_ob TEXT NOT NULL
        )
    """)
    
    # Create predictions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_obs_time INTEGER UNIQUE,    -- Timestamp of observation used to make prediction
            forecast_time INTEGER NOT NULL,   -- Target timestamp (input_obs_time + 3 hours)
            predicted_temperature REAL,
            predicted_pressure REAL,
            is_verified INTEGER DEFAULT 0,
            actual_temperature REAL,
            actual_pressure REAL,
            temp_error REAL,
            pressure_error REAL,
            temp_status TEXT,                 -- "MATCH" or "MISMATCH"
            pressure_status TEXT              -- "MATCH" or "MISMATCH"
        )
    """)

    # Create briefing_packages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS briefing_packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_time TEXT NOT NULL,
            departure_time TEXT NOT NULL,
            airport_code TEXT NOT NULL,
            area TEXT NOT NULL,
            flight_level TEXT NOT NULL,
            fly_hours INTEGER NOT NULL,
            metar_raw TEXT NOT NULL,
            taf_raw TEXT NOT NULL,
            chart_url TEXT NOT NULL,
            chart_file_path TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

def save_briefing_package(db_path, pkg):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO briefing_packages (
                request_time, departure_time, airport_code, area, 
                flight_level, fly_hours, metar_raw, taf_raw, 
                chart_url, chart_file_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pkg["request_time"], pkg["departure_time"], pkg["airport_code"], pkg["area"],
            pkg["flight_level"], pkg["fly_hours"], pkg["metar_raw"], pkg["taf_raw"],
            pkg["chart_url"], pkg["chart_file_path"]
        ))
        conn.commit()
        pkg_id = cursor.lastrowid
        conn.close()
        return pkg_id
    except Exception as e:
        print(f"Error saving briefing package: {e}")
        conn.close()
        return None

def get_briefing_packages(db_path, limit=20):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM briefing_packages
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_briefing_package_by_id(db_path, pkg_id):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM briefing_packages
        WHERE id = ?
    """, (pkg_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_observation(db_path, obs):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO observations (
                obs_time, report_time, temperature, humidity, pressure, 
                dew_point, wind_speed, wind_direction, visibility, raw_ob
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            obs["obs_time"], obs["report_time"], obs["temperature"], obs["humidity"], 
            obs["pressure"], obs["dew_point"], obs["wind_speed"], obs["wind_direction"], 
            obs["visibility"], obs["raw_ob"]
        ))
        conn.commit()
    except Exception as e:
        print(f"Error saving observation: {e}")
    finally:
        conn.close()

def save_prediction(db_path, pred):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO predictions (
                input_obs_time, forecast_time, predicted_temperature, predicted_pressure, is_verified
            ) VALUES (?, ?, ?, ?, 0)
        """, (
            pred["input_obs_time"], pred["forecast_time"], 
            pred["predicted_temperature"], pred["predicted_pressure"]
        ))
        conn.commit()
    except Exception as e:
        print(f"Error saving prediction: {e}")
    finally:
        conn.close()

def get_unverified_predictions(db_path):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM predictions 
        WHERE is_verified = 0
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def verify_prediction(db_path, pred_id, actual_temp, actual_pressure, temp_error, pressure_error, temp_status, pressure_status):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE predictions
            SET is_verified = 1,
                actual_temperature = ?,
                actual_pressure = ?,
                temp_error = ?,
                pressure_error = ?,
                temp_status = ?,
                pressure_status = ?
            WHERE id = ?
        """, (actual_temp, actual_pressure, temp_error, pressure_error, temp_status, pressure_status, pred_id))
        conn.commit()
    except Exception as e:
        print(f"Error verifying prediction: {e}")
    finally:
        conn.close()

def get_verification_history(db_path, limit=20):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    # Join with observations table to get the raw time context for the verification
    cursor.execute("""
        SELECT p.*, o.report_time as forecast_report_time
        FROM predictions p
        LEFT JOIN observations o ON p.forecast_time = o.obs_time
        WHERE p.is_verified = 1
        ORDER BY p.forecast_time DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_latest_forecast(db_path):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, o.report_time as input_report_time
        FROM predictions p
        LEFT JOIN observations o ON p.input_obs_time = o.obs_time
        ORDER BY p.input_obs_time DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_recent_observations(db_path, max_time, limit=10):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM observations
        WHERE obs_time <= ?
        ORDER BY obs_time DESC
        LIMIT ?
    """, (max_time, limit))
    rows = cursor.fetchall()
    conn.close()
    # Reverse to get chronological order (oldest first)
    return [dict(r) for r in reversed(rows)]
