import pandas as pd
import numpy as np
import joblib
import os
import random
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

# Load data
data_path = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")
df = pd.read_csv(data_path)

# Load model
model = joblib.load(os.path.join(PROJECT_DIR, "model", "weather_model.pkl"))
scaler = joblib.load(os.path.join(PROJECT_DIR, "model", "scaler.pkl"))
features = joblib.load(os.path.join(PROJECT_DIR, "model", "feature_columns.pkl"))

# Prepare data (🔥 IMPORTANT - y define here)
X = df[features]
y = df[["target_temperature", "target_humidity", "target_pressure"]]

# Scale
X_scaled = scaler.transform(X)

# Predict
y_pred = model.predict(X_scaled)

print("X shape:", X.shape)
print("y shape:", y.shape)
print("y_pred shape:", y_pred.shape)

# =========================
# 🔥 REAL vs PREDICTION TABLE
# =========================
print("\n🔍 Selecting 10 Random Samples for Verification...\n")

sample_size = min(10, len(y))
indices = random.sample(range(len(y)), sample_size)

y_actual = y.iloc[indices].values
y_pred_sample = y_pred[indices]

print("="*100)
print(f"{'MODEL VERIFICATION: REAL DATA vs AI PREDICTION':^100}")
print("="*100)

print(f"{'Sample #':<10} | {'Temp (Real)':<12} | {'Temp (Pred)':<12} | {'Error':<8} | "
      f"{'Humidity (Real)':<15} | {'Humidity (Pred)':<15} | {'Error':<8} | "
      f"{'Pressure (Real)':<15} | {'Pressure (Pred)':<15} | {'Error':<8}")

print("-"*100)

for i in range(sample_size):
    t_real = y_actual[i][0]
    t_pred = y_pred_sample[i][0]
    t_err = abs(t_real - t_pred)

    h_real = y_actual[i][1]
    h_pred = y_pred_sample[i][1]
    h_err = abs(h_real - h_pred)

    p_real = y_actual[i][2]
    p_pred = y_pred_sample[i][2]
    p_err = abs(p_real - p_pred)

    print(f"Test #{i+1:<4} | "
          f"{t_real:<12.2f} | {t_pred:<12.2f} | {t_err:<8.2f} | "
          f"{h_real:<15.2f} | {h_pred:<15.2f} | {h_err:<8.2f} | "
          f"{p_real:<15.2f} | {p_pred:<15.2f} | {p_err:<8.2f}")

print("="*100)
print("💡 Smaller error = better prediction accuracy")

# =========================
# 🔥 METRICS
# =========================
try:
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    r2 = r2_score(y, y_pred)
    accuracy = r2 * 100

    print("\n📊 MODEL PERFORMANCE")
    print("Overall RMSE:", rmse)
    print("R2 Score:", r2)
    print("Accuracy:", round(accuracy, 2), "%")

except Exception as e:
    print("❌ Error in evaluation:", str(e))