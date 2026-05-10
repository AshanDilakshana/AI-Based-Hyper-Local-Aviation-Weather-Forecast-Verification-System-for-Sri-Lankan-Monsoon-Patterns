import pandas as pd
import pickle
import os
import numpy as np
from xgboost import XGBRegressor, XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error

# 1. Path Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Loading from the processed CSV
DATA_FILE = os.path.join(BASE_DIR, '../../data/aviation_weather_features.csv')
MODEL_SAVE_PATH = BASE_DIR 

def train_xgboost_fast():
    if not os.path.exists(DATA_FILE):
        print(f"❌ Error: Data file not found at {DATA_FILE}")
        return

    print(f"📂 Loading Data for XGBoost...")
    
    try:
        df = pd.read_csv(DATA_FILE)
        df.columns = df.columns.str.strip()

        # Feature selection
        feature_cols = ['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']
        X = df[feature_cols]
        y_vis = df['Visibility']
        y_cloud = df['Cloud_Status']

        # 2. Split Data
        X_train, X_test, y_vis_train, y_vis_test, y_cloud_train, y_cloud_test = train_test_split(
            X, y_vis, y_cloud, test_size=0.2, random_state=42
        )

        # 3. Fast Training (Using fixed parameters like other models)
        print("⏳ Training XGBoost models (Fast Mode)...")
        
        # Visibility Model
        model_vis = XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42)
        model_vis.fit(X_train, y_vis_train)
        
        # Cloud Model
        model_cloud = XGBClassifier(n_estimators=100, max_depth=6, random_state=42)
        model_cloud.fit(X_train, y_cloud_train)

        # 4. Accuracy & Performance Metrics
        vis_preds = model_vis.predict(X_test)
        cloud_preds = model_cloud.predict(X_test)

        cloud_acc = accuracy_score(y_cloud_test, cloud_preds) * 100
        vis_mae = mean_absolute_error(y_vis_test, vis_preds)

        print("\n" + "="*40)
        print("📊 XGBOOST RESULTS (FAST MODE)")
        print("="*40)
        print(f"✅ Cloud Accuracy: {cloud_acc:.2f}%")
        print(f"✅ Visibility MAE: {vis_mae:.2f} m")
        print("="*40)

        # 5. Save Models
        with open(os.path.join(MODEL_SAVE_PATH, 'xgboost_visibility.pkl'), 'wb') as f:
            pickle.dump(model_vis, f)
        with open(os.path.join(MODEL_SAVE_PATH, 'xgboost_cloud.pkl'), 'wb') as f:
            pickle.dump(model_cloud, f)

        print(f"🚀 Models saved successfully.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    train_xgboost_fast()