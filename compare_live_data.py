import sqlite3
import os
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'weather_data.db')

def update_and_display_comparisons():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Fetch pending predictions
    pending_query = "SELECT id, target_time_utc, model_type, predicted_value FROM dewpoint_qnh_predictions WHERE status = 'PENDING LIVE DATA'"
    pending_df = pd.read_sql_query(pending_query, conn)
    
    # 2. Check if live data has arrived for these targets
    # Assuming 'weather_data' table has 'timestamp_utc' and relevant columns
    for idx, row in pending_df.iterrows():
        target_time = row['target_time_utc']
        model_type = row['model_type']
        
        # Determine the column to look for in weather_data based on model_type
        if 'QNH' in model_type.upper():
            actual_col = 'qnh_hpa'
        elif 'DEWPOINT' in model_type.upper():
            actual_col = 'dew_point_c'
        else:
            continue
            
        # Check if there is a record in weather_data matching the target_time exactly
        # Weather data timestamps are often at the top of the hour or specific minutes, we do a direct match here.
        # Alternatively, we can use LIKE to match up to the hour.
        target_time_str = str(target_time)
        live_query = f"SELECT {actual_col} FROM weather_data WHERE timestamp_utc = '{target_time_str}' LIMIT 1"
        
        try:
            live_cursor = conn.cursor()
            live_cursor.execute(live_query)
            result = live_cursor.fetchone()
            
            if result and result[0] is not None:
                # Live data found!
                actual_val = float(result[0])
                predicted_val = float(row['predicted_value'])
                error = abs(actual_val - predicted_val)
                
                # Update status
                update_query = '''
                    UPDATE dewpoint_qnh_predictions 
                    SET status = ? 
                    WHERE id = ?
                '''
                status_str = f"{actual_val:.2f} (Error: {error:.2f})"
                conn.cursor().execute(update_query, (status_str, row['id']))
                conn.commit()
        except sqlite3.OperationalError:
            # Maybe the weather_data table doesn't have the exact structure expected here, ignore and keep pending
            pass

    # 3. Print the formatted table
    final_query = "SELECT target_time_utc, model_type, predicted_value, status FROM dewpoint_qnh_predictions ORDER BY target_time_utc DESC LIMIT 20"
    final_df = pd.read_sql_query(final_query, conn)
    conn.close()
    
    print("=" * 85)
    print(f"{'Target Time (UTC)':<20} | {'Forecast Type':<16} | {'Predicted':<18} | {'Actual'}")
    print("=" * 85)
    
    if final_df.empty:
        print("No records found.")
    else:
        for _, row in final_df.iterrows():
            t_time = str(row['target_time_utc'])
            # Formatting time slightly to match screenshot layout if needed (e.g. remove seconds)
            if len(t_time) > 16:
                t_time = t_time[:16] # e.g. '2026-08-19 14:10'
            t_time = t_time.replace(":", "") # e.g. '2026-08-19 1410'
            
            f_type = str(row['model_type'])
            pred = f"{float(row['predicted_value']):.2f}"
            act = str(row['status'])
            
            print(f"{t_time:<20} | {f_type:<16} | {pred:<18} | {act}")

if __name__ == "__main__":
    update_and_display_comparisons()
