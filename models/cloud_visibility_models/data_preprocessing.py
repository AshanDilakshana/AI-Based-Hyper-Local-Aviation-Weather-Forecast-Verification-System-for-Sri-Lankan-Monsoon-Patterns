import os
import pickle

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.abspath(os.path.join(BASE_DIR, '../../data/BIA_METAR_DATA_(2019_2024).xlsx'))
OUTPUT_PATH = os.path.abspath(os.path.join(BASE_DIR, '../../data/aviation_weather_features.csv'))

def preprocess_metar_data():
    print(" Loading original METAR dataset...")
    if not os.path.exists(INPUT_PATH):
        print(f"Error: Input file not found at {INPUT_PATH}")
        return

    df = pd.read_excel(INPUT_PATH)
    df.columns = df.columns.str.strip()

    print(" Cleaning data fields and processing strings...")
    df['Visibility'] = df['Visibility'].astype(str).str.strip().replace('', np.nan)
    df['Clouds'] = df['Clouds'].astype(str).str.strip().fillna('NSC')
    df['Weather'] = df['Weather'].astype(str).str.strip().fillna('NONE')

    # 1. Temporal Features
    df['Month'] = pd.to_numeric(df['Month'], errors='coerce')
    df['Time(UTC)'] = pd.to_numeric(df['Time(UTC)'], errors='coerce')
    df['Hour'] = df['Time(UTC)'] // 100
    
    # 2. Wind Direction
    df['Wind Dir.'] = pd.to_numeric(df['Wind Dir.'], errors='coerce')

    # Numerical Coercion
    for col in ['Dry tem(0C)', 'Dew point(0C)', 'RH(%)', 'QNH (hPa)', 'Wind speed(Kts)', 'Visibility']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 3. Weather Column Encoding
    print(" Encoding Weather Column and saving encoder...")
    weather_encoder = LabelEncoder()
    df['Weather_Encoded'] = weather_encoder.fit_transform(df['Weather'])
    
    save_models_dir = os.path.abspath(os.path.join(BASE_DIR, '../saved_models'))
    os.makedirs(save_models_dir, exist_ok=True)
    with open(os.path.join(save_models_dir, 'weather_encoder.pkl'), 'wb') as f:
        pickle.dump(weather_encoder, f)

    # Drop missing base rows
    required_base = ['Dry tem(0C)', 'Dew point(0C)', 'RH(%)', 'QNH (hPa)', 'Wind speed(Kts)', 'Visibility', 'Clouds', 'Month', 'Hour', 'Wind Dir.']
    df = df.dropna(subset=required_base)

    print(" Executing Advanced Interaction Feature Engineering...")
    df['Dew_Point_Depression'] = df['Dry tem(0C)'] - df['Dew point(0C)']
    df['Temp_RH'] = df['Dry tem(0C)'] * df['RH(%)']
    df['Wind_RH'] = df['Wind speed(Kts)'] * df['RH(%)']
    df['Pressure_Wind'] = df['QNH (hPa)'] * df['Wind speed(Kts)']
    df['RH_Squared'] = df['RH(%)'] ** 2

    # Formatting Target Columns exactly as Strings/Categories
    df['Visibility_Cleaned'] = df['Visibility'].astype(int).astype(str)
    df['Cloud_Cleaned'] = df['Clouds']

    print(f"Saving processed dataset (14 features) to {OUTPUT_PATH}...")
    df.to_csv(OUTPUT_PATH, index=False)
    print("[SUCCESS] Preprocessing and Feature Engineering Complete!")


if __name__ == "__main__":
    preprocess_metar_data()