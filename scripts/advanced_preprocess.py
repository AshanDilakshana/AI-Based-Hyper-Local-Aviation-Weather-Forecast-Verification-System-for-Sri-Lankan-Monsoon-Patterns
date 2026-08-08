import pandas as pd
import numpy as np
import os

def run_preprocessing():
    # Path Setup
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # Moves up from /scripts/ to root

    filename = "BIA_METAR_DATA_(2019_2024).xlsx"
    input_path = os.path.join(PROJECT_ROOT, 'data', filename)
    
    qnh_output_path = os.path.join(PROJECT_ROOT, 'data', 'data_qnh.csv')
    rh_output_path = os.path.join(PROJECT_ROOT, 'data', 'data_rh.csv')

    print(f"Researcher: P.K.V.K. Jayathilaka | Separating QNH and RH Features...")

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found!")
        return

    df = pd.read_excel(input_path, engine='openpyxl')
    
    # 1. Clean Data & Remove Outliers
    df['RH(%)'] = pd.to_numeric(df['RH(%)'], errors='coerce')
    df['QNH (hPa)'] = pd.to_numeric(df['QNH (hPa)'], errors='coerce')
    df['Dry tem(0C)'] = pd.to_numeric(df['Dry tem(0C)'], errors='coerce')
    df['Dew point(0C)'] = pd.to_numeric(df['Dew point(0C)'], errors='coerce')
    df['Wind speed(Kts)'] = pd.to_numeric(df['Wind speed(Kts)'], errors='coerce').fillna(0)
    
    # Filter Outliers
    df.loc[(df['QNH (hPa)'] < 950) | (df['QNH (hPa)'] > 1050), 'QNH (hPa)'] = np.nan
    df.loc[(df['RH(%)'] < 0) | (df['RH(%)'] > 100), 'RH(%)'] = np.nan
    df.loc[(df['Dry tem(0C)'] < 0) | (df['Dry tem(0C)'] > 50), 'Dry tem(0C)'] = np.nan
    df.loc[(df['Dew point(0C)'] < 0) | (df['Dew point(0C)'] > 50), 'Dew point(0C)'] = np.nan
    
    df = df.ffill().bfill()

    # 2. General Engineering
    df['hour'] = np.arange(len(df)) % 24
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24.0)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24.0)
    df['temp_spread'] = df['Dry tem(0C)'] - df['Dew point(0C)']
    df['stability_index'] = df['RH(%)'] / df['QNH (hPa)']

    # 3. Targets
    df['target_qnh'] = df['QNH (hPa)'].shift(-3)
    df['target_rh'] = df['RH(%)'].shift(-3)

    # ---------------------------------------------------------
    # QNH Specific Feature Engineering
    # ---------------------------------------------------------
    df_qnh = df.copy()
    df_qnh['qnh_momentum'] = df_qnh['QNH (hPa)'].diff(periods=1)
    df_qnh['qnh_lag_1'] = df_qnh['QNH (hPa)'].shift(1)
    df_qnh['qnh_lag_2'] = df_qnh['QNH (hPa)'].shift(2)
    df_qnh['qnh_rolling_3'] = df_qnh['QNH (hPa)'].rolling(window=3).mean()
    df_qnh['qnh_rolling_6'] = df_qnh['QNH (hPa)'].rolling(window=6).mean()
    
    # Select only QNH relevant columns
    qnh_cols = ['QNH (hPa)', 'Dry tem(0C)', 'temp_spread', 'hour_sin', 'hour_cos', 
                'qnh_momentum', 'qnh_lag_1', 'qnh_lag_2', 'qnh_rolling_3', 'qnh_rolling_6', 'target_qnh']
    df_qnh = df_qnh[qnh_cols].dropna()
    df_qnh.to_csv(qnh_output_path, index=False)

    # ---------------------------------------------------------
    # RH Specific Feature Engineering
    # ---------------------------------------------------------
    df_rh = df.copy()
    df_rh['rh_momentum'] = df_rh['RH(%)'].diff(periods=1)
    df_rh['rh_lag_1'] = df_rh['RH(%)'].shift(1)
    df_rh['rh_lag_2'] = df_rh['RH(%)'].shift(2)
    df_rh['rh_rolling_3'] = df_rh['RH(%)'].rolling(window=3).mean()
    
    # Select only RH relevant columns
    rh_cols = ['RH(%)', 'Dry tem(0C)', 'Dew point(0C)', 'temp_spread', 'hour_sin', 'hour_cos', 
               'rh_momentum', 'rh_lag_1', 'rh_lag_2', 'rh_rolling_3', 'Wind speed(Kts)', 'target_rh']
    df_rh = df_rh[rh_cols].dropna()
    df_rh.to_csv(rh_output_path, index=False)

    print(f"Success: 'data_qnh.csv' and 'data_rh.csv' created with separated features.")

if __name__ == "__main__":
    run_preprocessing()