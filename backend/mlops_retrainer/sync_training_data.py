import pandas as pd
from backend.data.database import engine as supabase_engine, sqlite_engine
from sqlalchemy import text
import datetime


def sync_training_data():
    """
    Just-In-Time (JIT) Database Sync for Model Retraining.
    Pulls new weather_data from Supabase and appends it to the local SQLite cache.
    """
    print("[INFO] Starting JIT Sync for MLOps Training Data...")

    try:
        # Get the latest timestamp in the local SQLite database
        with sqlite_engine.connect() as sqlite_conn:
            result = sqlite_conn.execute(
                text("SELECT MAX(timestamp_utc) FROM weather_data")
            ).fetchone()
            last_timestamp_str = result[0] if result else None

        if last_timestamp_str:
            print(f"[INFO] Latest local data timestamp: {last_timestamp_str}")
            query = f"SELECT * FROM weather_data WHERE timestamp_utc > '{last_timestamp_str}' ORDER BY timestamp_utc ASC"
        else:
            two_years_ago = (
                datetime.datetime.utcnow() - datetime.timedelta(days=365 * 2)
            ).strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"[INFO] No local data found. Fetching initial dataset (Last 2 years from {two_years_ago})..."
            )
            query = f"SELECT * FROM weather_data WHERE timestamp_utc >= '{two_years_ago}' ORDER BY timestamp_utc ASC"

        # Fetch new data from Supabase
        new_data = pd.read_sql_query(query, supabase_engine)

        if not new_data.empty:
            print(f"[INFO] Fetched {len(new_data)} new records from Supabase.")
            # Append to SQLite
            new_data.to_sql(
                "weather_data", sqlite_engine, if_exists="append", index=False
            )
            print("[SUCCESS] Local SQLite cache updated successfully!")
        else:
            print(
                "[INFO] Local SQLite cache is already up-to-date. No new data to sync."
            )

        return True

    except Exception as e:
        print(f"[ERROR] Failed to sync training data: {e}")
        return False


if __name__ == "__main__":
    sync_training_data()
