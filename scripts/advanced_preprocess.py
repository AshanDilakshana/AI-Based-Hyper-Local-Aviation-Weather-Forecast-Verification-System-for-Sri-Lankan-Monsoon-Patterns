import pandas as pd
import numpy as np
import os

def run_preprocessing():
    # Path Setup - Adjusted to your specific folder structure
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # Moves up from /scripts/ to root

    filename = "BIA_METAR_DATA_(2019_2024).xlsx"
    input_path = os.path.join(PROJECT_ROOT, 'data', filename)
    output_path = os.path.join(PROJECT_ROOT, 'data', 'advanced_multi_data.csv')

    print(f"Researcher: P.K.V.K. Jayathilaka | Generating Features...")

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found!")
        return

    df = pd.read_excel(input_path, engine='openpyxl')
    
    # 1. Clean Data
    df['RH(%)'] = pd.to_numeric(df['RH(%)'], errors='coerce')
    df['QNH (hPa)'] = pd.to_numeric(df['QNH (hPa)'], errors='coerce')
    df['Dry tem(0C)'] = pd.to_numeric(df['Dry tem(0C)'], errors='coerce')
    df['Dew point(0C)'] = pd.to_numeric(df['Dew point(0C)'], errors='coerce')
    df = df.ffill().bfill()

    # 2. Engineering (The missing columns are created here)
    df['stability_index'] = df['RH(%)'] / df['QNH (hPa)']
    df['hour'] = np.arange(len(df)) % 24
    
    # MOMENTUM COLUMNS (The ones causing the error)
    df['qnh_momentum'] = df['QNH (hPa)'].diff(periods=1)
    df['rh_momentum'] = df['RH(%)'].diff(periods=1)

    # 3. Targets
    df['target_qnh'] = df['QNH (hPa)'].shift(-3)
    df['target_rh'] = df['RH(%)'].shift(-3)

    df = df.dropna()
    df.to_csv(output_path, index=False)
    print(f"✅ Success: 'advanced_multi_data.csv' created with all features.")

if __name__ == "__main__":
    run_preprocessing()