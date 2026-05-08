import pandas as pd
import numpy as np
import joblib
import os

from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from tensorflow.keras.models import load_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

data_path = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")

if not os.path.exists(data_path):
    raise FileNotFoundError(f"Dataset not found: {data_path}")

df = pd.read_csv(data_path)
y_real = df[["target_temperature", "target_pressure"]]

rf_dir = BASE_DIR
lstm_dir = os.path.join(BASE_DIR, "Lstm_model")
auto_dir = os.path.join(BASE_DIR, "autoencoder_model")


def check_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")


def metrics(name, y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)

    print(f"{name:<20} {round(mae, 3):<12} {round(rmse, 3):<12} {round(r2, 3):<12} {round(r2 * 100, 2):<12}")


# ================= RANDOM FOREST =================
check_file(os.path.join(rf_dir, "weather_model.pkl"))
check_file(os.path.join(rf_dir, "scaler.pkl"))
check_file(os.path.join(rf_dir, "feature_columns.pkl"))

rf_model = joblib.load(os.path.join(rf_dir, "weather_model.pkl"))
rf_scaler = joblib.load(os.path.join(rf_dir, "scaler.pkl"))
rf_features = joblib.load(os.path.join(rf_dir, "feature_columns.pkl"))

missing_rf = [col for col in rf_features if col not in df.columns]
if missing_rf:
    raise ValueError(f"RF missing columns in dataset: {missing_rf}")

X_rf = df[rf_features]
rf_pred = rf_model.predict(rf_scaler.transform(X_rf))


# ================= LSTM =================
check_file(os.path.join(lstm_dir, "lstm_weather_model.keras"))
check_file(os.path.join(lstm_dir, "lstm_x_scaler.pkl"))
check_file(os.path.join(lstm_dir, "lstm_y_scaler.pkl"))
check_file(os.path.join(lstm_dir, "lstm_feature_columns.pkl"))
check_file(os.path.join(lstm_dir, "lstm_time_steps.pkl"))

lstm_model = load_model(os.path.join(lstm_dir, "lstm_weather_model.keras"))
lstm_x_scaler = joblib.load(os.path.join(lstm_dir, "lstm_x_scaler.pkl"))
lstm_y_scaler = joblib.load(os.path.join(lstm_dir, "lstm_y_scaler.pkl"))
lstm_features = joblib.load(os.path.join(lstm_dir, "lstm_feature_columns.pkl"))
time_steps = joblib.load(os.path.join(lstm_dir, "lstm_time_steps.pkl"))

missing_lstm = [col for col in lstm_features if col not in df.columns]
if missing_lstm:
    raise ValueError(f"LSTM missing columns in dataset: {missing_lstm}")

X_lstm_scaled = lstm_x_scaler.transform(df[lstm_features])

X_seq = []
for i in range(time_steps, len(X_lstm_scaled)):
    X_seq.append(X_lstm_scaled[i - time_steps:i])

X_seq = np.array(X_seq)
y_lstm_real = y_real.iloc[time_steps:].values

lstm_pred_scaled = lstm_model.predict(X_seq)
lstm_pred = lstm_y_scaler.inverse_transform(lstm_pred_scaled)


# ================= AUTOENCODER =================
check_file(os.path.join(auto_dir, "autoencoder_weather_model.keras"))
check_file(os.path.join(auto_dir, "autoencoder_x_scaler.pkl"))
check_file(os.path.join(auto_dir, "autoencoder_y_scaler.pkl"))
check_file(os.path.join(auto_dir, "autoencoder_feature_columns.pkl"))

auto_model = load_model(os.path.join(auto_dir, "autoencoder_weather_model.keras"))
auto_x_scaler = joblib.load(os.path.join(auto_dir, "autoencoder_x_scaler.pkl"))
auto_y_scaler = joblib.load(os.path.join(auto_dir, "autoencoder_y_scaler.pkl"))
auto_features = joblib.load(os.path.join(auto_dir, "autoencoder_feature_columns.pkl"))

missing_auto = [col for col in auto_features if col not in df.columns]
if missing_auto:
    raise ValueError(f"Autoencoder missing columns in dataset: {missing_auto}")

auto_pred_scaled = auto_model.predict(auto_x_scaler.transform(df[auto_features]))
auto_pred = auto_y_scaler.inverse_transform(auto_pred_scaled)


# ================= FINAL REPORT =================
print("\n" + "=" * 85)
print(" FULL DATASET MODEL ACCURACY + ERROR CHECK ")
print("=" * 85)
print(f"{'Model':<20} {'MAE':<12} {'RMSE':<12} {'R2 Score':<12} {'Accuracy':<12}")
print("-" * 85)

metrics("Random Forest", y_real, rf_pred)
metrics("LSTM", y_lstm_real, lstm_pred)
metrics("Autoencoder", y_real, auto_pred)

print("=" * 85)
print("LSTM Time Steps Used:", time_steps)