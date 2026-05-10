import pandas as pd
import numpy as np
import os

# 1. Setup Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Path to the original Excel file
INPUT_PATH = os.path.join(BASE_DIR, '../data/BIA_METAR_DATA_(2019_2024).xlsx')
# Path to save the processed CSV
OUTPUT_PATH = os.path.join(BASE_DIR, '../data/aviation_weather_features.csv')

def preprocess_metar_data():
    print("📂 Loading original METAR dataset...")
    
    if not os.path.exists(INPUT_PATH):
        print(f"❌ Error: Input file not found at {INPUT_PATH}")
        return

    # 2. Load Dataset
    df = pd.read_excel(INPUT_PATH)
    
    # Cleaning column names (Removing leading/trailing spaces)
    df.columns = df.columns.str.strip()

    # 3. Feature Selection & Cleaning
    # Columns required for our AI model
    required_columns = ['Dry tem(0C)', 'Dew point(0C)', 'RH(%)', 'QNH (hPa)', 'Visibility', 'Clouds']
    
    print("🧹 Cleaning data and handling missing values...")
    
    # Convert numerical columns and handle errors
    for col in ['Dry tem(0C)', 'Dew point(0C)', 'RH(%)', 'QNH (hPa)', 'Visibility']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows where essential weather data is missing
    df.dropna(subset=['Dry tem(0C)', 'Dew point(0C)', 'RH(%)', 'QNH (hPa)', 'Visibility'], inplace=True)

    # 4. Feature Engineering
    print("⚙️ Generating new features (Dew Point Depression)...")
    # Calculating Dew_Point_Depression (Crucial for Cloud/Visibility prediction)
    df['Dew_Point_Depression'] = df['Dry tem(0C)'] - df['Dew point(0C)']

    # 5. Cloud Label Encoding (Converting text to numbers for the Model)
    print("🏷️ Encoding Cloud labels...")
    
    def encode_clouds(cloud_str):
        cloud_str = str(cloud_str).upper()
        if 'OVC' in cloud_str: return 0
        if 'BKN' in cloud_str: return 1
        if 'SCT' in cloud_str: return 2
        if 'FEW' in cloud_str: return 3
        return 4  # NSC, SKC, CAVOK, etc.

    df['Cloud_Status'] = df['Clouds'].apply(encode_clouds)

    # 6. Save the Processed Data
    print(f"💾 Saving processed data to {OUTPUT_PATH}...")
    
    # We keep 'Clouds' and 'Visibility' for verification purposes
    df.to_csv(OUTPUT_PATH, index=False)
    
    print("✅ Preprocessing Complete! File is ready for Training and Verification.")

if __name__ == "__main__":
    preprocess_metar_data()