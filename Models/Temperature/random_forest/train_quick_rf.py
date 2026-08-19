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
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))  # Project root
MODEL_DIR = os.path.join(PROJECT_DIR, "model")

input_path = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")
df = pd.read_csv(input_path)

drop_cols = [
    "datetime",
    "future_time",
    "target_temperature",
    "target_humidity",
    "target_pressure"
]

X = df.drop(columns=drop_cols, errors="ignore")
y_temp = df["target_temperature"]
y_press = df["target_pressure"]

X = X.select_dtypes(include=[np.number])
X = X.replace([np.inf, -np.inf], np.nan)
X = X.fillna(X.mean())

y_temp = y_temp.replace([np.inf, -np.inf], np.nan)
y_temp = y_temp.fillna(y_temp.mean())

y_press = y_press.replace([np.inf, -np.inf], np.nan)
y_press = y_press.fillna(y_press.mean())

# Split chronologically
X_train, X_test, y_temp_train, y_temp_test = train_test_split(
    X, y_temp, test_size=0.2, shuffle=False
)
_, _, y_press_train, y_press_test = train_test_split(
    X, y_press, test_size=0.2, shuffle=False
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
press_pred = press_model.predict(X_test_press_scaled)
press_r2 = r2_score(y_press_test, press_pred)
press_mae = mean_absolute_error(y_press_test, press_pred)

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
