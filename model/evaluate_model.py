import pandas as pd
import numpy as np
import joblib
import os

from tensorflow.keras.models import load_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

data_path = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")

if not os.path.exists(data_path):
    raise FileNotFoundError(f"Dataset not found: {data_path}")

df = pd.read_csv(data_path)

# ================= RANDOM FOREST FILES =================
rf_model_path = os.path.join(BASE_DIR, "weather_model.pkl")
rf_scaler_path = os.path.join(BASE_DIR, "scaler.pkl")
rf_features_path = os.path.join(BASE_DIR, "feature_columns.pkl")

for path in [rf_model_path, rf_scaler_path, rf_features_path]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")

rf_model = joblib.load(rf_model_path)
rf_scaler = joblib.load(rf_scaler_path)
rf_features = joblib.load(rf_features_path)

# ================= SAMPLE 10 ROWS =================
test_sample = df.head(10).copy()

missing_rf = [col for col in rf_features if col not in test_sample.columns]
if missing_rf:
    raise ValueError(f"Missing columns in dataset: {missing_rf}")

X_sample = test_sample[rf_features]
X_sample_scaled = rf_scaler.transform(X_sample)

# ================= PREDICTION =================
rf_pred = rf_model.predict(X_sample_scaled)

test_sample["Predicted_Temperature"] = rf_pred[:, 0]
test_sample["Predicted_Pressure"] = rf_pred[:, 1]

# ================= VERIFICATION DISPLAY =================
print("\n" + "=" * 130)
print("      BIA AVIATION WEATHER - TEMPERATURE & PRESSURE VERIFICATION RESULTS")
print("=" * 130)

print(
    f"{'Row':<5} | "
    f"{'Actual Temp':<12} | {'Pred Temp':<12} | {'Temp Error':<12} | {'Temp Status':<12} | "
    f"{'Actual Pressure':<16} | {'Pred Pressure':<16} | {'Pressure Error':<16} | {'Pressure Status':<15}"
)

print("-" * 130)

for index, row in test_sample.iterrows():

    actual_temp = float(row["target_temperature"])
    pred_temp = float(row["Predicted_Temperature"])

    actual_pressure = float(row["target_pressure"])
    pred_pressure = float(row["Predicted_Pressure"])

    # ================= ERROR =================
    temp_error = abs(actual_temp - pred_temp)
    pressure_error = abs(actual_pressure - pred_pressure)

    # ================= MATCH STATUS =================
    temp_status = "MATCH" if temp_error <= 2 else "MISMATCH"
    pressure_status = "MATCH" if pressure_error <= 3 else "MISMATCH"

    print(
        f"{index + 1:<5} | "
        f"{actual_temp:<12.2f} | "
        f"{pred_temp:<12.2f} | "
        f"{temp_error:<12.2f} | "
        f"{temp_status:<12} | "
        f"{actual_pressure:<16.2f} | "
        f"{pred_pressure:<16.2f} | "
        f"{pressure_error:<16.2f} | "
        f"{pressure_status:<15}"
    )

print("=" * 130)
print("Verification process completed.")