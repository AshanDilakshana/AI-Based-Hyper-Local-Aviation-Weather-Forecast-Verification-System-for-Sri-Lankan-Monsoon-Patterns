import os
import pickle
import sqlite3
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../'))
db_path = os.path.abspath(os.path.join(project_root, '../weather_data.db'))

print(f"[INFO] Random Forest Script: Loading dataset from DB {db_path}...")

conn = sqlite3.connect(db_path)
df = pd.read_sql_query("SELECT * FROM weather_data", conn)
conn.close()

# Calculate derived features
df['Hour'] = pd.to_datetime(df['timestamp_utc'], format='mixed', utc=True).dt.hour
df['Dew_Point_Depression'] = df['dry_temp_c'] - df['dew_point_c']

def clean_cloud(text):
    text = str(text).upper()
    if any(x in text for x in ['BKN', 'OVC']): return 'CLOUDY'
    if any(x in text for x in ['SCT', 'FEW']): return 'PARTLY_CLOUDY'
    if any(x in text for x in ['NSC', 'SKC', 'CLR', 'NIL']): return 'CLEAR'
    return 'OTHER'

df['Cloud_Cleaned'] = df['clouds'].apply(clean_cloud)

# Rename to match original feature list
df.rename(columns={
    'wind_speed_kts': 'Wind speed(Kts)',
    'dry_temp_c': 'Dry tem(0C)',
    'dew_point_c': 'Dew point(0C)',
    'rh_percent': 'RH(%)',
    'qnh_hpa': 'QNH (hPa)',
    'visibility': 'Visibility_Cleaned'
}, inplace=True)

features = ['Dry tem(0C)', 'Dew point(0C)', 'RH(%)', 'QNH (hPa)', 'Wind speed(Kts)', 'Dew_Point_Depression']
df = df.dropna(subset=features + ['Cloud_Cleaned', 'Visibility_Cleaned'])

df['Cloud_Code'] = df['Cloud_Cleaned'].astype('category').cat.codes
cloud_mapping = dict(enumerate(df['Cloud_Cleaned'].astype('category').cat.categories))

df['Vis_Code'] = df['Visibility_Cleaned'] # Maintain continuous values

X = df[features]
y_cloud = df['Cloud_Code']
y_vis = df['Vis_Code']

save_path = os.path.join(project_root, 'Models', 'saved_models')
os.makedirs(save_path, exist_ok=True)

print("\n[TRAINING] Training Bundled Random Forest Models (Cloud + Visibility together)...")
X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, y_cloud, test_size=0.2, random_state=42)
X_train_v, X_test_v, y_train_v, y_test_v = train_test_split(X, y_vis, test_size=0.2, random_state=42)

# Cloud Classifier
cloud_model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42, n_jobs=-1)
cloud_model.fit(X_train_c, y_train_c)

# Visibility Regressor
vis_model = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42, n_jobs=-1)
vis_model.fit(X_train_v, y_train_v)

# Predict both
c_preds = cloud_model.predict(X_test_c)
v_preds = vis_model.predict(X_test_v)

cloud_acc = accuracy_score(y_test_c, c_preds)
vis_mae = mean_absolute_error(y_test_v, v_preds)

print(f"\n[RESULTS] Random Forest Bundled Model:")
print(f"  -> Cloud Classification Accuracy: {cloud_acc * 100:.2f}%")
print(f"  -> Visibility Mean Absolute Error (MAE): {vis_mae:.4f}")

bundled_model = {
    'cloud_model': cloud_model,
    'vis_model': vis_model,
    'cloud_mapping': cloud_mapping
}

with open(os.path.join(save_path, 'random_forest_multi_model.pkl'), 'wb') as f:
    pickle.dump(bundled_model, f)

print("[SUCCESS] Bundled Random Forest model saved!")