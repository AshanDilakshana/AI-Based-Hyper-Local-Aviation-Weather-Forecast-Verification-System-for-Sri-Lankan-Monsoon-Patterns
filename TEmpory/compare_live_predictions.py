import os
import sys
import pandas as pd
from sqlalchemy import create_engine

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../'))
DB_PATH = os.path.join(project_root, 'weather_data.db')

def compare_predictions():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    
    # Load all prediction records
    predictions = pd.read_sql("SELECT * FROM prediction_records ORDER BY created_at DESC", engine)
    
    if predictions.empty:
        print("No predictions found in the database. Please make a prediction via the frontend/API first.")
        return
        
    print(f"Found {len(predictions)} saved predictions.\n")
    
    # Load recent weather data for matching
    actuals = pd.read_sql("SELECT * FROM weather_data ORDER BY id DESC LIMIT 500", engine)
    
    print("="*80)
    print(f"{'Target Time (UTC)':<20} | {'Forecast Type':<15} | {'Predicted (Kts)':<18} | {'Actual (Kts)':<15}")
    print("="*80)
    
    matched_count = 0
    pending_count = 0
    
    for _, row in predictions.iterrows():
        # Match by date and time
        try:
            target_year = int(row['target_year'])
            target_month = int(row['target_month'])
            target_date = int(row['target_date'])
            target_time = str(row['target_time_utc']).zfill(4)
            predicted_speed = float(row['predicted_wind_speed_kts'])
            forecast_type = row['forecast_type']
            
            target_datetime_str = f"{target_year}-{target_month:02d}-{target_date:02d} {target_time}"
        except (ValueError, TypeError):
            # Skip records with missing or invalid date/time fields
            continue
        
        # Search in actuals
        match = actuals[
            (actuals['year'] == target_year) &
            (actuals['month'] == target_month) &
            (actuals['date'] == target_date) &
            (actuals['time_utc'] == target_time)
        ]
        
        if not match.empty:
            actual_speed = float(match.iloc[0]['wind_speed_kts'])
            error = abs(predicted_speed - actual_speed)
            
            # Format output
            actual_str = f"{actual_speed:.2f} (Error: {error:.2f})"
            print(f"{target_datetime_str:<20} | {forecast_type:<15} | {predicted_speed:<18.2f} | {actual_str:<15}")
            matched_count += 1
        else:
            print(f"{target_datetime_str:<20} | {forecast_type:<15} | {predicted_speed:<18.2f} | PENDING LIVE DATA")
            pending_count += 1
            
    print("="*80)
    print(f"Total: {matched_count} Verified, {pending_count} Pending.")

if __name__ == "__main__":
    compare_predictions()
