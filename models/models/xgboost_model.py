import pandas as pd
import pickle
import os
import numpy as np
from xgboost import XGBRegressor, XGBClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder

# Path configuration
BASE_DIR = r'C:\Users\USER\Desktop\Research_IT22619976\AI-Based-Hyper-Local-Aviation-Weather-Forecast-Verification-System-for-Sri-Lankan-Monsoon-Patterns'
DATA_FILE = os.path.join(BASE_DIR, 'data', 'BIA_METAR_DATA_(2019_2024).xlsx')
MODEL_SAVE_PATH = os.path.join(BASE_DIR, 'models', 'models')

def train_takeoff_model_optimized():
    if not os.path.exists(DATA_FILE):
        print(f"❌ Error: Excel file not found at {DATA_FILE}")
        return

    print(f"📂 Loading and Cleaning Excel data...")
    
    try:
        # Load XLSX
        df = pd.read_excel(DATA_FILE, sheet_name='Sheet1')
        
        # 1. Cleaning Column Names
        df.columns = df.columns.str.strip()

        # 2. Data Type Conversion (අකුරු තියෙන තැන් වලට NaN දාලා අංක බවට හරවමු)
        cols_to_fix = ['Dry tem(0C)', 'Dew point(0C)', 'RH(%)', 'QNH (hPa)', 'Visibility']
        for col in cols_to_fix:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 3. Drop rows with missing values (වැරදි දත්ත පේළි අයින් කිරීම)
        df = df.dropna(subset=cols_to_fix)

        # 4. Feature Engineering (Take-off එකට අදාළව)
        df['Dew_Point_Depression'] = df['Dry tem(0C)'] - df['Dew point(0C)']
        
        feature_cols = ['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']
        X = df[feature_cols]
        y_vis = df['Visibility']
        
        # Cloud Status Encode කිරීම
        le = LabelEncoder()
        df['Clouds'] = df['Clouds'].astype(str).fillna('NSC')
        y_cloud = le.fit_transform(df['Clouds'])

        # 5. Split Data
        X_train, X_test, y_vis_train, y_vis_test, y_cloud_train, y_cloud_test = train_test_split(
            X, y_vis, y_cloud, test_size=0.1, random_state=42
        )

        print(f"⏳ Training with {len(X_train)} valid records using GridSearchCV...")

        # 6. Grid Search for Visibility 
        model_vis = XGBRegressor(tree_method='hist', random_state=42)
        param_grid = {
            "n_estimators": [800, 1000, 1200],
            "max_depth": [18, 22, 25],
            "learning_rate": [0.01, 0.05],
            "subsample": [0.8, 0.9],
            "colsample_bytree": [0.8, 0.9]
        }

        grid_search = GridSearchCV(
            estimator=model_vis,
            param_grid=param_grid,
            scoring="r2",
            cv=3,
            verbose=1,
            n_jobs=-1
        )

        grid_search.fit(X_train, y_vis_train)
        
        # 7. Training Cloud Classification
        cloud_model = XGBClassifier(n_estimators=1000, max_depth=15, random_state=42)
        cloud_model.fit(X_train, y_cloud_train)

        # 8. Save Models
        if not os.path.exists(MODEL_SAVE_PATH): os.makedirs(MODEL_SAVE_PATH)
        
        with open(os.path.join(MODEL_SAVE_PATH, 'xgboost_visibility.pkl'), 'wb') as f:
            pickle.dump(grid_search.best_estimator_, f)
        with open(os.path.join(MODEL_SAVE_PATH, 'xgboost_cloud.pkl'), 'wb') as f:
            pickle.dump(cloud_model, f)
        with open(os.path.join(MODEL_SAVE_PATH, 'label_encoder.pkl'), 'wb') as f:
            pickle.dump(le, f)

        print(f"✅ Success! Take-off models optimized and saved.")
        print(f"📊 Best Parameters: {grid_search.best_params_}")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    train_takeoff_model_optimized()