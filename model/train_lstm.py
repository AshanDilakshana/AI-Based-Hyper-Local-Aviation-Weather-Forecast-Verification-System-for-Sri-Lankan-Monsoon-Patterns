import pandas as pd
import numpy as np
import joblib
import os
import random
import tensorflow as tf

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam

random.seed(42)
np.random.seed(42)
tf.random.set_seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

input_path = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")
df = pd.read_csv(input_path)

drop_cols = [
    "datetime",
    "target_temperature",
    "target_humidity",
    "target_pressure"
]

X = df.drop(columns=drop_cols, errors="ignore")

y = df[[
    "target_temperature",
    "target_pressure"
]]

x_scaler = MinMaxScaler()
y_scaler = MinMaxScaler()

X_scaled = x_scaler.fit_transform(X)
y_scaled = y_scaler.fit_transform(y)

time_steps = 12

def create_sequences(X, y, time_steps):
    X_seq = []
    y_seq = []

    for i in range(time_steps, len(X)):
        X_seq.append(X[i-time_steps:i])
        y_seq.append(y[i])

    return np.array(X_seq), np.array(y_seq)

X_seq, y_seq = create_sequences(X_scaled, y_scaled, time_steps)

split_index = int(len(X_seq) * 0.8)

X_train = X_seq[:split_index]
X_test = X_seq[split_index:]

y_train = y_seq[:split_index]
y_test = y_seq[split_index:]

model = Sequential()

model.add(LSTM(
    units=128,
    return_sequences=True,
    input_shape=(X_train.shape[1], X_train.shape[2])
))
model.add(BatchNormalization())
model.add(Dropout(0.15))

model.add(LSTM(
    units=64,
    return_sequences=True
))
model.add(BatchNormalization())
model.add(Dropout(0.15))

model.add(LSTM(
    units=32,
    return_sequences=False
))
model.add(Dropout(0.1))

model.add(Dense(64, activation="relu"))
model.add(Dense(32, activation="relu"))
model.add(Dense(2))

model.compile(
    optimizer=Adam(learning_rate=0.0003),
    loss="mse",
    metrics=["mae"]
)

early_stop = EarlyStopping(
    monitor="val_loss",
    patience=25,
    restore_best_weights=True
)

reduce_lr = ReduceLROnPlateau(
    monitor="val_loss",
    factor=0.5,
    patience=8,
    min_lr=0.00001
)

history = model.fit(
    X_train,
    y_train,
    epochs=300,
    batch_size=8,
    validation_split=0.2,
    callbacks=[early_stop, reduce_lr],
    verbose=1
)

y_pred_scaled = model.predict(X_test)

y_pred = y_scaler.inverse_transform(y_pred_scaled)
y_test_original = y_scaler.inverse_transform(y_test)

print("Temperature MAE:",
      mean_absolute_error(y_test_original[:, 0], y_pred[:, 0]))

print("Pressure MAE:",
      mean_absolute_error(y_test_original[:, 1], y_pred[:, 1]))

print("Overall RMSE:",
      np.sqrt(mean_squared_error(y_test_original, y_pred)))

print("Overall R2 Score:",
      r2_score(y_test_original, y_pred))

model.save(os.path.join(BASE_DIR, "lstm_weather_model.keras"))

joblib.dump(x_scaler, os.path.join(BASE_DIR, "lstm_x_scaler.pkl"))
joblib.dump(y_scaler, os.path.join(BASE_DIR, "lstm_y_scaler.pkl"))
joblib.dump(list(X.columns), os.path.join(BASE_DIR, "lstm_feature_columns.pkl"))
joblib.dump(time_steps, os.path.join(BASE_DIR, "lstm_time_steps.pkl"))

print("\n✅ Tuned LSTM Model trained & saved successfully!")
print("Saved in:", BASE_DIR)
print("Time steps used:", time_steps)
print("Features used:", list(X.columns))