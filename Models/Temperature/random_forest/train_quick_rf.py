import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error, r2_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(BASE_DIR)))  # Project root
MODEL_DIR = BASE_DIR  # Save models in the random_forest folder

import sqlite3

db_path = os.path.join(PROJECT_DIR, "weather_data_.db")
conn = sqlite3.connect(db_path)
df = pd.read_sql_query("SELECT * FROM weather_data", conn)
conn.close()

# Sort chronologically
if 'timestamp_utc' in df.columns:
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], format='mixed', utc=True)
    df = df.sort_values('timestamp_utc').reset_index(drop=True)
else:
    df = df.sort_values('id').reset_index(drop=True)

# Generate target variables for forecasting (next step)
df['target_temperature'] = df['dry_temp_c'].shift(-1)
df['target_pressure'] = df['qnh_hpa'].shift(-1)
df['target_pressure_diff'] = df['target_pressure'] - df['qnh_hpa']

# Generate lag features to give the model history
for i in range(1, 4):
    df[f'qnh_hpa_lag_{i}'] = df['qnh_hpa'].shift(i)
    df[f'dry_temp_c_lag_{i}'] = df['dry_temp_c'].shift(i)
    df[f'rh_percent_lag_{i}'] = df['rh_percent'].shift(i)

# Drop rows which will have NaN targets or NaN lag features
df = df.dropna(subset=[
    'target_temperature', 'target_pressure',
    'qnh_hpa_lag_1', 'qnh_hpa_lag_2', 'qnh_hpa_lag_3'
])

drop_cols = [
    "id",
    "timestamp_utc",
    "datetime",
    "future_time",
    "target_temperature",
    "target_humidity",
    "target_pressure",
    "target_pressure_diff"
]

X = df.drop(columns=drop_cols, errors="ignore")
y_temp = df["target_temperature"]
y_press_diff = df["target_pressure_diff"]
y_press_abs = df["target_pressure"]

X = X.select_dtypes(include=[np.number])
X = X.replace([np.inf, -np.inf], np.nan)
X = X.fillna(X.mean())

y_temp = y_temp.replace([np.inf, -np.inf], np.nan)
y_temp = y_temp.fillna(y_temp.mean())

y_press_diff = y_press_diff.replace([np.inf, -np.inf], np.nan)
y_press_diff = y_press_diff.fillna(y_press_diff.mean())

# Split chronologically
X_train, X_test, y_temp_train, y_temp_test = train_test_split(
    X, y_temp, test_size=0.2, shuffle=False
)
_, _, y_press_train, y_press_diff_test = train_test_split(
    X, y_press_diff, test_size=0.2, shuffle=False
)
_, _, y_press_abs_train, y_press_abs_test = train_test_split(
    X, y_press_abs, test_size=0.2, shuffle=False
)

# Scale separately
temp_scaler = StandardScaler()
X_train_temp_scaled = temp_scaler.fit_transform(X_train)
X_test_temp_scaled = temp_scaler.transform(X_test)

press_scaler = StandardScaler()
X_train_press_scaled = press_scaler.fit_transform(X_train)
X_test_press_scaled = press_scaler.transform(X_test)

print("Training quick baseline models separately...")

# Train Temperature model
print("Training Temperature Model...")
temp_model = RandomForestRegressor(
    n_estimators=100,
    max_depth=15,
    random_state=42,
    n_jobs=-1
)
temp_model.fit(X_train_temp_scaled, y_temp_train)

# Train Pressure model
print("Training Pressure Model...")
press_model = RandomForestRegressor(
    n_estimators=100,
    max_depth=15,
    random_state=42,
    n_jobs=-1
)
press_model.fit(X_train_press_scaled, y_press_train)

# Evaluate Temperature model
temp_pred = temp_model.predict(X_test_temp_scaled)
temp_r2 = r2_score(y_temp_test, temp_pred)
temp_mae = mean_absolute_error(y_temp_test, temp_pred)

# Evaluate Pressure model
press_diff_pred = press_model.predict(X_test_press_scaled)
# Reconstruct absolute pressure from predicted diff + current pressure
current_pressure_test = X_test['qnh_hpa'].values
press_pred_abs = current_pressure_test + press_diff_pred

press_r2 = r2_score(y_press_abs_test, press_pred_abs)
press_mae = mean_absolute_error(y_press_abs_test, press_pred_abs)

print("--- SEPARATE RANDOM FOREST PERFORMANCE ---")
print(f"Temperature - MAE: {temp_mae:.4f}, R2 Score: {temp_r2:.4f}")
print(f"Pressure    - MAE: {press_mae:.4f}, R2 Score: {press_r2:.4f}")

# Save the trained models, scalers and features
joblib.dump(temp_model, os.path.join(MODEL_DIR, "temp_model.pkl"))
joblib.dump(temp_scaler, os.path.join(MODEL_DIR, "temp_scaler.pkl"))
joblib.dump(list(X.columns), os.path.join(MODEL_DIR, "temp_feature_columns.pkl"))

joblib.dump(press_model, os.path.join(MODEL_DIR, "pressure_model.pkl"))
joblib.dump(press_scaler, os.path.join(MODEL_DIR, "pressure_scaler.pkl"))
joblib.dump(list(X.columns), os.path.join(MODEL_DIR, "pressure_feature_columns.pkl"))

print("Separate models saved successfully!")
