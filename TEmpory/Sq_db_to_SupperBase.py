import os
import pandas as pd
from sqlalchemy import create_engine
from supabase import create_client, Client
import math
import dateutil.parser

# ==========================================
# SUPABASE CONFIGURATION
# ==========================================
SUPABASE_URL = "https://otsdxvkstsfforfssrvr.supabase.co"
SUPABASE_KEY = "sb_secret_Pulak7uR2aCrJwq8vjQr_w_RGC6AqIb"

TABLES_CONFIG = {
    'weather_data': {
        'unique_cols': ['year', 'month', 'date', 'time_utc'],
        'time_cols': [],
        'limit': 1000,
        'order_by': 'id DESC'
    },
    'system_logs': {
        'unique_cols': ['timestamp_utc', 'component', 'message'],
        'time_cols': ['timestamp_utc'],
        'limit': None,
        'order_by': None
    },
    'prediction_records': {
        'unique_cols': ['target_year', 'target_month', 'target_date', 'target_time_utc', 'forecast_type'],
        'time_cols': [],
        'limit': None,
        'order_by': None
    },
    'verified_forecasts': {
        'unique_cols': ['target_time', 'created_at'],
        'time_cols': ['target_time', 'created_at'],
        'limit': None,
        'order_by': None
    }
}

def normalize_timestamp(val):
    """Normalize datetime strings from SQLite and Supabase to a common ISO format for accurate comparison."""
    if val is None or pd.isna(val):
        return ""
    try:
        dt = dateutil.parser.parse(str(val))
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    except:
        return str(val).strip()

def sync_table(supabase: Client, engine, table_name, config):
    print(f"\n==========================================")
    print(f"--- Syncing Table: {table_name} ---")
    
    unique_cols = config['unique_cols']
    time_cols = config['time_cols']
    limit = config['limit']
    order_by = config['order_by']
    
    # 1. Fetch Local Data
    query = f"SELECT * FROM {table_name}"
    if order_by:
        query += f" ORDER BY {order_by}"
    if limit:
        query += f" LIMIT {limit}"
        
    df_local = pd.read_sql(query, engine)
    
    if df_local.empty:
        print(f"No records found in local SQLite table '{table_name}'.")
        return
        
    if 'time_utc' in df_local.columns:
        df_local['time_utc_clean'] = df_local['time_utc'].astype(str).str.zfill(4)
        
    # 2. Fetch Existing Keys from Supabase to completely prevent duplicates
    print(f"🔍 Fetching existing keys for '{table_name}' from Supabase...")
    existing_keys = set()
    start = 0
    fetch_limit = 1000
    
    select_str = ", ".join(unique_cols)
    
    while True:
        try:
            res = supabase.table(table_name).select(select_str).range(start, start + fetch_limit - 1).execute()
            data = res.data
            if not data:
                break
            for row in data:
                try:
                    key_parts = []
                    for col in unique_cols:
                        val = row.get(col)
                        if col == 'time_utc' and val is not None:
                            val = str(val).zfill(4)
                        elif col in time_cols:
                            val = normalize_timestamp(val)
                        key_parts.append(str(val))
                    existing_keys.add(tuple(key_parts))
                except Exception:
                    continue
            if len(data) < fetch_limit:
                break
            start += fetch_limit
        except Exception as e:
            print(f"   Warning: Could not fetch keys for {table_name} (Maybe table doesn't exist in Supabase yet?): {e}")
            break
            
    print(f"   Found {len(existing_keys)} unique records in Supabase.")
    
    # 3. Filter New Rows
    new_rows = []
    print("⚙️ Finding new records to insert...")
    for _, row in df_local.iterrows():
        try:
            key_parts = []
            for col in unique_cols:
                val = row['time_utc_clean'] if col == 'time_utc' and 'time_utc_clean' in row else row[col]
                if col in time_cols:
                    val = normalize_timestamp(val)
                key_parts.append(str(val))
            key = tuple(key_parts)
            
            if key not in existing_keys:
                row_dict = row.to_dict()
                if 'id' in row_dict:
                    del row_dict['id'] # Remove SQLite id to prevent Supabase clashes
                if 'time_utc_clean' in row_dict:
                    del row_dict['time_utc_clean']
                    
                # Replace NaN/NaT AND empty strings with None for JSON parsing
                for k, v in row_dict.items():
                    if pd.isna(v) or str(v).strip() == "":
                        row_dict[k] = None
                        
                # Convert timestamps to string format natively supported by json
                for tc in time_cols:
                    if row_dict.get(tc):
                        row_dict[tc] = str(row_dict[tc])
                        
                new_rows.append(row_dict)
                existing_keys.add(key)
        except Exception as e:
            continue
            
    print(f"📊 Summary for '{table_name}':")
    print(f"   - Local records fetched: {len(df_local)}")
    print(f"   - New non-duplicate records to send: {len(new_rows)}")
    
    if not new_rows:
        print(f"🎉 Table '{table_name}' is already 100% up-to-date!")
        return
        
    # 4. Upload in chunks
    print(f"🚀 Uploading new records to Supabase...")
    chunk_size = 500
    total_chunks = math.ceil(len(new_rows) / chunk_size)
    
    for i in range(0, len(new_rows), chunk_size):
        chunk = new_rows[i:i+chunk_size]
        current_chunk = (i // chunk_size) + 1
        print(f"   Uploading chunk {current_chunk}/{total_chunks} ({len(chunk)} records)...")
        try:
            supabase.table(table_name).insert(chunk).execute()
        except Exception as e:
            print(f"   ❌ Error uploading chunk {current_chunk}: {e}")

def sync_sqlite_to_supabase():
    print("🔌 Connecting to Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '../'))
    db_path = os.path.join(project_root, 'weather_data.db')
    
    print(f"📖 Connecting to local SQLite database at:\n   {db_path}")
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Run sync for each configured table
    for table_name, config in TABLES_CONFIG.items():
        sync_table(supabase, engine, table_name, config)
        
    print("\n✅ Successfully synchronized all tables to Supabase Cloud Database!")

if __name__ == "__main__":
    sync_sqlite_to_supabase()
