import os
import sys
import pandas as pd
from sqlalchemy import create_engine
from supabase import create_client, Client

# ==========================================
# SUPABASE CONFIGURATION
# ==========================================
SUPABASE_URL = "https://otsdxvkstsfforfssrvr.supabase.co"
SUPABASE_KEY = "sb_secret_Pulak7uR2aCrJwq8vjQr_w_RGC6AqIb"

def fetch_and_sync_supabase_to_local():
    print("🔌 Connecting to Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 1. Connect to local SQLite database
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '../'))
    db_path = os.path.join(project_root, 'weather_data.db')
    
    print(f"📖 Connecting to local SQLite database at:\n   {db_path}")
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Load recent records from local SQLite to create a set of existing keys for fast lookup
    print("🔍 Fetching recent record keys from local SQLite database...")
    try:
        existing_df = pd.read_sql("SELECT year, month, date, time_utc FROM weather_data ORDER BY id DESC LIMIT 2000", engine)
        # Create a set of tuples: (year, month, date, time_utc_str)
        existing_keys = set(
            zip(
                existing_df['year'].astype(int),
                existing_df['month'].astype(int),
                existing_df['date'].astype(int),
                existing_df['time_utc'].astype(str).str.zfill(4)
            )
        )
        print(f"   Found {len(existing_keys)} recent unique records in local SQLite DB.")
    except Exception as e:
        print(f"   Note/Warning when reading local SQLite: {e}")
        existing_keys = set()

    # 2. Fetch the latest 1000 weather_data records from Supabase
    print("\n☁️ Fetching latest 1000 weather_data records from Supabase Cloud Database...")
    response = supabase.table('weather_data').select('*').order('id', desc=True).limit(1000).execute()
    all_supabase_rows = response.data or []
    
    # Sort chronologically (oldest to newest)
    all_supabase_rows = list(reversed(all_supabase_rows))
        
    print(f"✅ Total latest records fetched from Supabase: {len(all_supabase_rows)}")
    
    if not all_supabase_rows:
        print("No records found in Supabase.")
        return

    # Convert to DataFrame
    supabase_df = pd.DataFrame(all_supabase_rows)
    
    # Standardize time_utc format (zfill to 4 digits)
    supabase_df['time_utc_clean'] = supabase_df['time_utc'].astype(str).str.zfill(4)
    
    # 3. Filter out duplicate records
    new_rows = []
    for _, row in supabase_df.iterrows():
        try:
            y = int(row['year'])
            m = int(row['month'])
            d = int(row['date'])
            t = str(row['time_utc_clean'])
            key = (y, m, d, t)
            
            if key not in existing_keys:
                new_rows.append(row)
                existing_keys.add(key) # Prevent duplicate entries within the batch
        except Exception:
            continue
            
    print(f"\n📊 Summary:")
    print(f"   - Total fetched from Supabase: {len(supabase_df)}")
    print(f"   - New non-duplicate records to insert: {len(new_rows)}")
    
    if not new_rows:
        print("🎉 Local SQLite database is already 100% up-to-date! No new data to insert.")
        return
        
    new_df = pd.DataFrame(new_rows)
    
    # Ensure correct columns mapping for SQLite weather_data table
    columns_to_keep = [
        'timestamp_utc', 'year', 'month', 'date', 'time_utc',
        'wind_dir', 'wind_speed_kts', 'visibility', 'weather', 'clouds',
        'dry_temp_c', 'dew_point_c', 'rh_percent', 'qnh_hpa'
    ]
    
    avail_cols = [col for col in columns_to_keep if col in new_df.columns]
    insert_df = new_df[avail_cols].copy()
    
    # Insert new rows into SQLite
    print(f"💾 Inserting {len(insert_df)} new records into local SQLite database...")
    insert_df.to_sql('weather_data', engine, if_exists='append', index=False)
    print("✅ Successfully synchronized Supabase data to local SQLite database!")

if __name__ == "__main__":
    fetch_and_sync_supabase_to_local()
