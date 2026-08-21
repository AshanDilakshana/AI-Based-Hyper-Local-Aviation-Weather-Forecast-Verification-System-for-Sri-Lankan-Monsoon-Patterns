import os
import sqlite3
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
DB_PATH = os.path.join(PROJECT_DIR, "weather_data.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "lstm_hybrid")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Load Data
print("Loading data from database...")
conn = sqlite3.connect(DB_PATH)
query = """
SELECT year, month, date, time_utc, dry_temp_c, qnh_hpa 
FROM weather_data 
ORDER BY year, month, date, time_utc
"""
df = pd.read_sql_query(query, conn)
conn.close()

# 2. Preprocess Data
print(f"Initial shape: {df.shape}")
# Ensure numeric
df['dry_temp_c'] = pd.to_numeric(df['dry_temp_c'], errors='coerce')
df['qnh_hpa'] = pd.to_numeric(df['qnh_hpa'], errors='coerce')

# Interpolate missing values
df['dry_temp_c'] = df['dry_temp_c'].interpolate(method='linear').ffill().bfill()
df['qnh_hpa'] = df['qnh_hpa'].interpolate(method='linear').ffill().bfill()

# Assuming data is 30 mins interval.
# T+3 hours = 6 steps ahead.
# Previous 6 hours = 12 steps.
STEPS_AHEAD = 6
SEQ_LEN = 12

df['target_temp'] = df['dry_temp_c'].shift(-STEPS_AHEAD)
df['target_press'] = df['qnh_hpa'].shift(-STEPS_AHEAD)

df = df.dropna()
print(f"Shape after shifting and dropping NA: {df.shape}")

# Limit data if too large for quick training (Optional, but using all 120k is fine)
# Let's use the last 50,000 to keep it manageable if needed, but we will use all to be accurate.
# df = df.tail(50000).reset_index(drop=True)

# 3. Create Sequences
features = df[['dry_temp_c', 'qnh_hpa']].values
targets = df[['target_temp', 'target_press']].values

scaler_X = StandardScaler()
features_scaled = scaler_X.fit_transform(features)

scaler_y = StandardScaler()
targets_scaled = scaler_y.fit_transform(targets)

X_seq, y_seq, current_features = [], [], []

print("Building sequences...")
for i in range(len(features_scaled) - SEQ_LEN):
    X_seq.append(features_scaled[i : i + SEQ_LEN])
    y_seq.append(targets_scaled[i + SEQ_LEN - 1]) # The target corresponds to the end of the sequence
    current_features.append(features[i + SEQ_LEN - 1]) # Unscaled current T/P for the Hybrid RF later

X_seq = np.array(X_seq)
y_seq = np.array(y_seq)
current_features = np.array(current_features)
targets_unscaled = targets[SEQ_LEN - 1 : len(targets) - 1]

# Chronological split
split_idx = int(len(X_seq) * 0.8)

X_train, X_test = X_seq[:split_idx], X_seq[split_idx:]
y_train, y_test = y_seq[:split_idx], y_seq[split_idx:]
curr_train, curr_test = current_features[:split_idx], current_features[split_idx:]
target_train_unscaled, target_test_unscaled = targets_unscaled[:split_idx], targets_unscaled[split_idx:]

# 4. Train LSTM
print("Training LSTM...")
lstm_model = Sequential([
    LSTM(64, activation='relu', input_shape=(SEQ_LEN, 2), return_sequences=False),
    Dropout(0.2),
    Dense(32, activation='relu'),
    Dense(2) # temp, pressure
])

lstm_model.compile(optimizer='adam', loss='mse')

early_stop = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

lstm_model.fit(
    X_train, y_train,
    epochs=10, # Keep epochs low for reasonable training time
    batch_size=64,
    validation_split=0.1,
    callbacks=[early_stop],
    verbose=1
)

# 5. Evaluate LSTM
lstm_preds_scaled = lstm_model.predict(X_test)
lstm_preds = scaler_y.inverse_transform(lstm_preds_scaled)

print("\n--- LSTM PERFORMANCE ---")
print("Temp MAE:", mean_absolute_error(target_test_unscaled[:, 0], lstm_preds[:, 0]))
print("Temp RMSE:", np.sqrt(mean_squared_error(target_test_unscaled[:, 0], lstm_preds[:, 0])))
print("Temp R2:", r2_score(target_test_unscaled[:, 0], lstm_preds[:, 0]))
print("Temp Accuracy:", 100 * (1 - mean_absolute_percentage_error(target_test_unscaled[:, 0], lstm_preds[:, 0])), "%")

print("Press MAE:", mean_absolute_error(target_test_unscaled[:, 1], lstm_preds[:, 1]))
print("Press RMSE:", np.sqrt(mean_squared_error(target_test_unscaled[:, 1], lstm_preds[:, 1])))
print("Press R2:", r2_score(target_test_unscaled[:, 1], lstm_preds[:, 1]))
print("Press Accuracy:", 100 * (1 - mean_absolute_percentage_error(target_test_unscaled[:, 1], lstm_preds[:, 1])), "%")

# 6. Train Hybrid RF
print("\nPreparing Hybrid RF features...")
# We need LSTM predictions for the training set to train the RF
lstm_preds_train_scaled = lstm_model.predict(X_train)
lstm_preds_train = scaler_y.inverse_transform(lstm_preds_train_scaled)

# Hybrid Features: [Current Temp, Current Press, LSTM Pred Temp, LSTM Pred Press]
hybrid_X_train = np.hstack((curr_train, lstm_preds_train))
hybrid_X_test = np.hstack((curr_test, lstm_preds))

print("Training Hybrid RF...")
rf = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
hybrid_model = MultiOutputRegressor(rf)
hybrid_model.fit(hybrid_X_train, target_train_unscaled)

# 7. Evaluate Hybrid RF
hybrid_preds = hybrid_model.predict(hybrid_X_test)

print("\n--- HYBRID LSTM + RF PERFORMANCE ---")
print("Temp MAE:", mean_absolute_error(target_test_unscaled[:, 0], hybrid_preds[:, 0]))
print("Temp RMSE:", np.sqrt(mean_squared_error(target_test_unscaled[:, 0], hybrid_preds[:, 0])) )
print("Temp R2:", r2_score(target_test_unscaled[:, 0], hybrid_preds[:, 0]))
print("Temp Accuracy:", 100 * (1 - mean_absolute_percentage_error(target_test_unscaled[:, 0], hybrid_preds[:, 0])), "%")

print("Press MAE:", mean_absolute_error(target_test_unscaled[:, 1], hybrid_preds[:, 1]))
print("Press RMSE:", np.sqrt(mean_squared_error(target_test_unscaled[:, 1], hybrid_preds[:, 1])))
print("Press R2:", r2_score(target_test_unscaled[:, 1], hybrid_preds[:, 1]))
print("Press Accuracy:", 100 * (1 - mean_absolute_percentage_error(target_test_unscaled[:, 1], hybrid_preds[:, 1])), "%")

# 8. Save Models
lstm_model.save(os.path.join(OUTPUT_DIR, "lstm_model.keras"))
joblib.dump(hybrid_model, os.path.join(OUTPUT_DIR, "hybrid_rf_model.pkl"))
joblib.dump(scaler_X, os.path.join(OUTPUT_DIR, "lstm_scaler_X.pkl"))
joblib.dump(scaler_y, os.path.join(OUTPUT_DIR, "lstm_scaler_y.pkl"))

print(f"\nModels saved successfully in {OUTPUT_DIR}!")
