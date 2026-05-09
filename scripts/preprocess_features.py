import pandas as pd
import numpy as np
import os

def preprocess_and_engineer_features():
    # 1. Setup Path
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
    
    # Updated to the exact .xlsx filename found by your terminal
    filename = "BIA_METAR_DATA_(2019_2024).xlsx"
    input_path = os.path.join(PROJECT_ROOT, 'data', filename)
    output_path = os.path.join(PROJECT_ROOT, 'data', 'processed_features.csv')

    print(f"Checking for file at: {input_path}")

    if not os.path.exists(input_path):
        print(f"ERROR: File not found at {input_path}")
        return

    # 2. Load Data (Changed to read_excel)
    print("File found! Loading Excel METAR data...")
    try:
        # We use engine='openpyxl' to handle .xlsx files
        df = pd.read_excel(input_path, engine='openpyxl')
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return
    
    # 3. Process Columns (Matching your METAR dataset headers)
    rh_col = 'RH(%)'
    qnh_col = 'QNH (hPa)'
    
    # Ensure columns exist
    if rh_col not in df.columns or qnh_col not in df.columns:
        print(f"Error: Could not find columns '{rh_col}' or '{qnh_col}'")
        print(f"Available columns are: {df.columns.tolist()}")
        return

    df[rh_col] = pd.to_numeric(df[rh_col], errors='coerce')
    df[qnh_col] = pd.to_numeric(df[qnh_col], errors='coerce')
    
    # Handle missing values (Forward fill for time-series continuity)
    df = df.ffill()
    
    # 4. Feature Engineering for Second Inter-Monsoon (SIM)
    print("Engineering monsoon stability features...")
    
    # Rate of change over 3 steps
    df['qnh_drop_3h'] = df[qnh_col].diff(periods=3)
    df['rh_change_3h'] = df[rh_col].diff(periods=3)
    
    # Pressure-Humidity interaction (Crucial for SIM stability analysis)
    df['rh_qnh_interaction'] = df[rh_col] / df[qnh_col]
    
    # Target: The QNH change in the next 3 steps (approx 1.5 - 3 hours)
    df['target_future_qnh_drop'] = df[qnh_col].shift(-3) - df[qnh_col]
    
    # Drop rows with NaN values created by shifting/diffing
    df = df.dropna()
    
    # 5. Save as CSV for Model Training
    df.to_csv(output_path, index=False)
    print(f"SUCCESS: Processed data saved to {output_path}")

if __name__ == "__main__":
    preprocess_and_engineer_features()