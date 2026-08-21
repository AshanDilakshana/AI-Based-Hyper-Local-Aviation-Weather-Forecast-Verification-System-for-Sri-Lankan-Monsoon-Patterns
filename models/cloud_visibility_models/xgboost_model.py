import os
import pickle
import sqlite3
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, accuracy_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor, XGBClassifier

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../'))
db_path = os.path.abspath(os.path.join(project_root, '../weather_data.db'))

print(f"[INFO] XGBoost Script: Loading dataset from DB {db_path}...")

conn = sqlite3.connect(db_path)
df = pd.read_sql_query("SELECT * FROM weather_data", conn)
conn.close()

# Calculate derived features
df['Hour'] = pd.to_datetime(df['timestamp_utc'], format='mixed', utc=True).dt.hour
df['Dew_Point_Depression'] = df['dry_temp_c'] - df['dew_point_c']
df['Temp_RH'] = df['dry_temp_c'] * df['rh_percent']
df['Wind_RH'] = df['wind_speed_kts'] * df['rh_percent']
df['Pressure_Wind'] = df['qnh_hpa'] * df['wind_speed_kts']
df['RH_Squared'] = df['rh_percent'] ** 2

# Encode weather
df['Weather_Encoded'] = df['weather'].astype('category').cat.codes

def clean_cloud(text):
    text = str(text).upper()
    if any(x in text for x in ['BKN', 'OVC']): return 'CLOUDY'
    if any(x in text for x in ['SCT', 'FEW']): return 'PARTLY_CLOUDY'
    if any(x in text for x in ['NSC', 'SKC', 'CLR', 'NIL']): return 'CLEAR'
    return 'OTHER'

df['Cloud_Cleaned'] = df['clouds'].apply(clean_cloud)

# Rename to match original feature list
df.rename(columns={
    'month': 'Month',
    'wind_dir': 'Wind Dir.',
    'wind_speed_kts': 'Wind speed(Kts)',
    'dry_temp_c': 'Dry tem(0C)',
    'dew_point_c': 'Dew point(0C)',
    'rh_percent': 'RH(%)',
    'qnh_hpa': 'QNH (hPa)',
    'visibility': 'Visibility_Cleaned'
}, inplace=True)

features = [
    'Month', 'Hour', 'Wind Dir.', 'Wind speed(Kts)', 'Dry tem(0C)', 'Dew point(0C)', 
    'RH(%)', 'QNH (hPa)', 'Dew_Point_Depression', 'Temp_RH', 'Wind_RH', 
    'Pressure_Wind', 'RH_Squared', 'Weather_Encoded'
]

df = df.dropna(subset=features + ['Cloud_Cleaned', 'Visibility_Cleaned'])

df['Cloud_Code'] = df['Cloud_Cleaned'].astype('category').cat.codes
cloud_mapping = dict(enumerate(df['Cloud_Cleaned'].astype('category').cat.categories))

df['Vis_Code'] = df['Visibility_Cleaned'] # Maintain continuous values for Regressor

X = df[features]
y_cloud = df['Cloud_Code']
y_vis = df['Vis_Code']

save_path = os.path.join(project_root, 'Models', 'saved_models')
os.makedirs(save_path, exist_ok=True)

print("\n[TRAINING] Optimizing and Training Bundled XGBoost Models (Cloud + Visibility together)...")
X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, y_cloud, test_size=0.2, random_state=42)
X_train_v, X_test_v, y_train_v, y_test_v = train_test_split(X, y_vis, test_size=0.2, random_state=42)

# Cloud Classifier (Highly Complex for >80% Accuracy)
cloud_model = XGBClassifier(
    n_estimators=500, 
    max_depth=12, 
    learning_rate=0.1,
    tree_method='hist', # PREVENTS RAM CRASH
    random_state=42,
    n_jobs=-1
)
cloud_model.fit(X_train_c, y_train_c)

# Visibility Regressor
vis_model = XGBRegressor(
    n_estimators=500, 
    max_depth=7, 
    learning_rate=0.04,
    subsample=0.8, 
    colsample_bytree=0.8, 
    random_state=42, 
    n_jobs=-1
)
vis_model.fit(X_train_v, y_train_v)

# Predict both
c_preds = cloud_model.predict(X_test_c)
v_preds = vis_model.predict(X_test_v)

cloud_acc = accuracy_score(y_test_c, c_preds)
vis_mae = mean_absolute_error(y_test_v, v_preds)

print(f"\n[RESULTS] XGBoost Bundled Model:")
print(f"  -> Cloud Classification Accuracy: {cloud_acc * 100:.2f}%")
print(f"  -> Visibility Mean Absolute Error (MAE): {vis_mae:.4f}")

# Bundle them into one dictionary
bundled_model = {
    'cloud_model': cloud_model,
    'vis_model': vis_model,
    'cloud_mapping': cloud_mapping
}

with open(os.path.join(save_path, 'xgb_multi_model.pkl'), 'wb') as f:
    pickle.dump(bundled_model, f)

print("[SUCCESS] Bundled XGBoost model saved to Models/saved_models/xgb_multi_model.pkl!")
