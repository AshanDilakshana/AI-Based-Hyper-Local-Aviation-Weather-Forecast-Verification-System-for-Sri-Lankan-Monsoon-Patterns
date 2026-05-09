import pandas as pd
import pickle
import os
import numpy as np
import gc # Used to clear RAM memory
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score

# 1. Path Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../"))
# Path to the data folder and Excel file
DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'BIA_METAR_DATA_(2019_2024).xlsx')
MODEL_SAVE_PATH = BASE_DIR 

def train_pure_weather_model():
    # Clear RAM memory to prevent allocation errors
    gc.collect()
    
    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: Dataset not found at {DATA_PATH}")
        return

    # 2. Load Dataset from Excel
    print("📂 Loading BIA METAR dataset (Pure Weather Parameters)...")
    try:
        df = pd.read_excel(DATA_PATH)
    except Exception as e:
        print(f"❌ Error reading Excel: {e}")
        return

    # Cleaning column names
    df.columns = df.columns.str.strip()

    # 3. Feature Selection: Removing Year, Month, Date, and Time
    # Using only meteorological data for the AI model
    features = ['Dry tem(0C)', 'Dew point(0C)', 'RH(%)', 'QNH (hPa)']
    
    for col in features + ['Visibility']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Fill missing cloud data and drop rows with empty weather values
    df['Clouds'] = df['Clouds'].fillna('NSC').astype(str).str.upper()
    df.dropna(subset=features + ['Visibility'], inplace=True)
    
    # Feature Engineering: Calculating Dew Point Depression
    df['Dew_Point_Depression'] = df['Dry tem(0C)'] - df['Dew point(0C)']

    # 4. Target Labeling: Mapping 5 standard cloud categories
    def extract_cloud_label(cloud_str):
        if 'OVC' in cloud_str: return 0
        if 'BKN' in cloud_str: return 1
        if 'SCT' in cloud_str: return 2
        if 'FEW' in cloud_str: return 3
        return 4 # NSC/SKC/CAVOK

    df['Cloud_Status'] = df['Clouds'].apply(extract_cloud_label)

    # Final inputs (X) and target outputs (y)
    X = df[['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']]
    y_vis = df['Visibility']
    y_cloud = df['Cloud_Status']

    # Free up RAM by deleting the dataframe after processing
    del df
    gc.collect()

    # 5. Split Data (80% Training, 20% Testing)
    X_train, X_test, y_v_train, y_v_test, y_c_train, y_c_test = train_test_split(
        X, y_vis, y_cloud, test_size=0.2, random_state=42
    )

    print("⏳ Training Lightweight Random Forest models...")

    # 6. Model Training (Restricting trees and depth to save RAM)
    cloud_model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    vis_model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)

    cloud_model.fit(X_train, y_c_train)
    vis_model.fit(X_train, y_v_train)

    # 7. Model Evaluation
    acc = accuracy_score(y_c_test, cloud_model.predict(X_test)) * 100

    print("\n" + "="*40)
    print("📊 MODEL TRAINING SUMMARY")
    print("="*40)
    print(f"✅ Cloud Accuracy: {acc:.2f}%")
    print("="*40)

    # 8. Exporting trained models as .pkl files
    with open(os.path.join(MODEL_SAVE_PATH, 'random_forest_visibility.pkl'), 'wb') as f:
        pickle.dump(vis_model, f)
    with open(os.path.join(MODEL_SAVE_PATH, 'random_forest_cloud.pkl'), 'wb') as f:
        pickle.dump(cloud_model, f)

    print("\n🚀 Training Complete! Models saved without Month/Time dependencies.")

if __name__ == "__main__":
    train_pure_weather_model()