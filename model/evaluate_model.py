import pandas as pd
import numpy as np
import joblib
import os

from sklearn.metrics import mean_squared_error, r2_score
from tensorflow.keras.models import load_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

data_path = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")
df = pd.read_csv(data_path)

y_real = df[[
    "target_temperature",
    "target_pressure"
]]

# ================= RANDOM FOREST =================

rf_model = joblib.load(os.path.join(BASE_DIR, "weather_model.pkl"))
rf_scaler = joblib.load(os.path.join(BASE_DIR, "scaler.pkl"))
rf_features = joblib.load(os.path.join(BASE_DIR, "feature_columns.pkl"))

rf_features = [f for f in rf_features if f in df.columns]

X_rf = df[rf_features]
X_rf_scaled = rf_scaler.transform(X_rf)
rf_pred = rf_model.predict(X_rf_scaled)

rf_rmse = np.sqrt(mean_squared_error(y_real, rf_pred))
rf_r2 = r2_score(y_real, rf_pred)

# ================= LSTM =================

lstm_model = load_model(os.path.join(BASE_DIR, "lstm_weather_model.keras"))
lstm_x_scaler = joblib.load(os.path.join(BASE_DIR, "lstm_x_scaler.pkl"))
lstm_y_scaler = joblib.load(os.path.join(BASE_DIR, "lstm_y_scaler.pkl"))
lstm_features = joblib.load(os.path.join(BASE_DIR, "lstm_feature_columns.pkl"))

lstm_features = [f for f in lstm_features if f in df.columns]

X_lstm = df[lstm_features]
X_lstm_scaled = lstm_x_scaler.transform(X_lstm)

time_steps_path = os.path.join(BASE_DIR, "lstm_time_steps.pkl")

if os.path.exists(time_steps_path):
    time_steps = joblib.load(time_steps_path)
else:
    time_steps = 6

X_seq = []

for i in range(time_steps, len(X_lstm_scaled)):
    X_seq.append(X_lstm_scaled[i-time_steps:i])

X_seq = np.array(X_seq)

y_lstm_real = y_real.iloc[time_steps:].values

lstm_pred_scaled = lstm_model.predict(X_seq)
lstm_pred = lstm_y_scaler.inverse_transform(lstm_pred_scaled)

lstm_rmse = np.sqrt(mean_squared_error(y_lstm_real, lstm_pred))
lstm_r2 = r2_score(y_lstm_real, lstm_pred)

# ================= AUTOENCODER =================

auto_model = load_model(os.path.join(BASE_DIR, "autoencoder_weather_model.keras"))
auto_x_scaler = joblib.load(os.path.join(BASE_DIR, "autoencoder_x_scaler.pkl"))
auto_y_scaler = joblib.load(os.path.join(BASE_DIR, "autoencoder_y_scaler.pkl"))
auto_features = joblib.load(os.path.join(BASE_DIR, "autoencoder_feature_columns.pkl"))

auto_features = [f for f in auto_features if f in df.columns]

X_auto = df[auto_features]
X_auto_scaled = auto_x_scaler.transform(X_auto)

auto_pred_scaled = auto_model.predict(X_auto_scaled)
auto_pred = auto_y_scaler.inverse_transform(auto_pred_scaled)

auto_rmse = np.sqrt(mean_squared_error(y_real, auto_pred))
auto_r2 = r2_score(y_real, auto_pred)

# ================= FINAL COMPARISON =================

print("\n" + "=" * 80)
print(" FINAL MODEL COMPARISON ")
print("=" * 80)

print(f"{'Model':<20} {'RMSE':<15} {'R2 Score':<15} {'Accuracy':<15}")
print("-" * 80)

print(f"{'Random Forest':<20} {round(rf_rmse, 3):<15} {round(rf_r2, 3):<15} {round(rf_r2 * 100, 2):<15}")
print(f"{'LSTM':<20} {round(lstm_rmse, 3):<15} {round(lstm_r2, 3):<15} {round(lstm_r2 * 100, 2):<15}")
print(f"{'Autoencoder':<20} {round(auto_rmse, 3):<15} {round(auto_r2, 3):<15} {round(auto_r2 * 100, 2):<15}")

print("=" * 80)
print("LSTM Time Steps Used:", time_steps)