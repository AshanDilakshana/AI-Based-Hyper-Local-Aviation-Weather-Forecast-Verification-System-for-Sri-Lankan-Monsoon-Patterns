import pandas as pd
import numpy as np
import joblib
import os
import random
import tensorflow as tf

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam

random.seed(42)
np.random.seed(42)
tf.random.set_seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))

input_path = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")

if not os.path.exists(input_path):
    raise FileNotFoundError(f"Dataset not found: {input_path}")

df = pd.read_csv(input_path)

df = df.replace([np.inf, -np.inf], np.nan)
df = df.fillna(df.mean(numeric_only=True))

selected_features = [
    "temperature",
    "humidity",
    "pressure",
    "dew_point",
    "wind_speed",
    "wind_direction",
    "visibility",
    "hour",
    "day",
    "month"
]

X = df[selected_features]
y = df[[
    "target_temperature",
    "target_pressure"
]]

split_index = int(len(X) * 0.8)

X_train_raw = X.iloc[:split_index]
X_test_raw = X.iloc[split_index:]

y_train_raw = y.iloc[:split_index]
y_test_raw = y.iloc[split_index:]

x_scaler = MinMaxScaler()
y_scaler = MinMaxScaler()

X_train_scaled = x_scaler.fit_transform(X_train_raw)
X_test_scaled = x_scaler.transform(X_test_raw)

y_train_scaled = y_scaler.fit_transform(y_train_raw)
y_test_scaled = y_scaler.transform(y_test_raw)

time_steps = 12  # Sequence length matches GRU (6 hours of history)

def create_sequences(X, y, time_steps):
    X_seq = []
    y_seq = []
    for i in range(time_steps, len(X)):
        X_seq.append(X[i - time_steps:i])
        y_seq.append(y[i])
    return np.array(X_seq), np.array(y_seq)

X_train, y_train = create_sequences(X_train_scaled, y_train_scaled, time_steps)
X_test, y_test = create_sequences(X_test_scaled, y_test_scaled, time_steps)

model = Sequential([
    Input(shape=(X_train.shape[1], X_train.shape[2])),
    LSTM(64, return_sequences=True),
    Dropout(0.2),
    LSTM(32, return_sequences=False),
    Dropout(0.2),
    Dense(16, activation="relu"),
    Dense(2)
])

model.compile(
    optimizer=Adam(learning_rate=0.001),
    loss="mse",
    metrics=["mae"]
)

early_stop = EarlyStopping(
    monitor="val_loss",
    patience=5,
    restore_best_weights=True
)

reduce_lr = ReduceLROnPlateau(
    monitor="val_loss",
    factor=0.8,
    patience=3,
    min_lr=0.00001
)

print("Training LSTM model...")
history = model.fit(
    X_train,
    y_train,
    epochs=20,
    batch_size=64,
    validation_split=0.2,
    callbacks=[early_stop, reduce_lr],
    verbose=1
)

y_pred_scaled = model.predict(X_test)

y_pred = y_scaler.inverse_transform(y_pred_scaled)
y_test_original = y_scaler.inverse_transform(y_test)

temp_mae = mean_absolute_error(y_test_original[:, 0], y_pred[:, 0])
temp_r2 = r2_score(y_test_original[:, 0], y_pred[:, 0])
pressure_mae = mean_absolute_error(y_test_original[:, 1], y_pred[:, 1])
pressure_r2 = r2_score(y_test_original[:, 1], y_pred[:, 1])
overall_rmse = np.sqrt(mean_squared_error(y_test_original, y_pred))
overall_r2 = r2_score(y_test_original, y_pred)

print("\nLSTM MODEL PERFORMANCE:")
print("Temperature MAE:", temp_mae)
print("Temperature R2 Score:", temp_r2)
print("Pressure MAE:", pressure_mae)
print("Pressure R2 Score:", pressure_r2)
print("Overall RMSE:", overall_rmse)
print("Overall R2 Score (average):", overall_r2)
print("Accuracy:", round(overall_r2 * 100, 2), "%")

# Save outputs
model.save(os.path.join(BASE_DIR, "lstm_weather_model.keras"))
joblib.dump(x_scaler, os.path.join(BASE_DIR, "lstm_x_scaler.pkl"))
joblib.dump(y_scaler, os.path.join(BASE_DIR, "lstm_y_scaler.pkl"))
joblib.dump(selected_features, os.path.join(BASE_DIR, "lstm_feature_columns.pkl"))
joblib.dump(time_steps, os.path.join(BASE_DIR, "lstm_time_steps.pkl"))

print("\nLSTM Model trained & saved successfully in:", BASE_DIR)