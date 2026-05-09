import pandas as pd
import numpy as np
import os

# --- PATH CONFIGURATION ---
# Using Absolute Path to avoid FileNotFoundError
BASE_DIR = r'C:\Users\USER\Desktop\Research_IT22619976\AI-Based-Hyper-Local-Aviation-Weather-Forecast-Verification-System-for-Sri-Lankan-Monsoon-Patterns'
INPUT_FILE = os.path.join(BASE_DIR, 'data', 'cleaned_data.csv')
OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'aviation_weather_features.csv')

def run_feature_engineering():
    print("⏳ Starting Feature Engineering...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: Input file not found at {INPUT_FILE}")
        return

    # 1. Load the cleaned data
    df = pd.read_csv(INPUT_FILE)

    # 2. Convert Aviation-Critical columns to numeric
    cols_to_fix = ['Dry tem(0C)', 'Dew point(0C)', 'RH(%)', 'QNH (hPa)', 'Visibility']
    for col in cols_to_fix:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 3. Data Optimization
    # Rounding to help the model identify consistent patterns
    df['Dry tem(0C)'] = df['Dry tem(0C)'].round(1)
    df['QNH (hPa)'] = df['QNH (hPa)'].round(1)

    # Capping visibility at 10,000m (Aviation Standard Max) to handle outliers
    df['Visibility'] = df['Visibility'].clip(upper=10000)

    # 4. Clouds Encoding: Mapping codes to numeric levels
    cloud_map = {'SKC': 0, 'NSC': 0, 'FEW': 1, 'SCT': 2, 'BKN': 3, 'OVC': 4}
    df['Cloud_Level'] = df['Clouds'].str[:3].map(cloud_map).fillna(0)

    # 5. Calculate Dew Point Depression (Key for Fog/Mist prediction)
    df['Dew_Point_Depression'] = df['Dry tem(0C)'] - df['Dew point(0C)']

    # 6. Define Target Variable for Visibility Safety
    df['Visibility_Status'] = np.where(df['Visibility'] < 5000, 1, 0)

    # 7. Selecting Final Features for Training
    final_features = [
        'Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 
        'QNH (hPa)', 'Visibility', 'Cloud_Level', 'Visibility_Status'
    ]

    # Drop rows with any missing takeoff-critical data
    df.dropna(subset=['Dew_Point_Depression', 'QNH (hPa)', 'RH(%)', 'Visibility'], inplace=True)

    # 8. Save the engineered dataset
    df[final_features].to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Success: Optimized data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_feature_engineering()