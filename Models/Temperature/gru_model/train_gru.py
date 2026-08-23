import os
import joblib
import numpy as np
import pandas as pd

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import GRU, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping

# ===============================
# PATHS
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
DATA_PATH = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")

# ===============================
# LOAD DATA
# ===============================
print("Loading dataset...")
df = pd.read_csv(DATA_PATH)
print("Dataset shape:", df.shape)

# ===============================
# FEATURES
# ===============================
drop_cols = [
    "datetime",
    "future_time",
    "target_temperature",
    "target_pressure",
    "target_humidity"
]

X = df.drop(columns=drop_cols, errors="ignore")
y = df[["target_temperature", "target_pressure"]]

# Select numeric features
X = X.select_dtypes(include=np.number)
X = X.fillna(X.mean())
y = y.fillna(y.mean())

# ===============================
# SCALING
# ===============================
X_scaler = MinMaxScaler()
y_scaler = MinMaxScaler()

X_scaled = X_scaler.fit_transform(X)
y_scaled = y_scaler.fit_transform(y)

# ===============================
# SEQUENCING
# ===============================
TIME_STEPS = 12  # 6 hours of meteorological observation history (highly optimal and fast)

def create_sequences(X, y):
    Xs = []
    ys = []
    for i in range(len(X) - TIME_STEPS):
        Xs.append(X[i:i + TIME_STEPS])
        ys.append(y[i + TIME_STEPS])
    return np.array(Xs), np.array(ys)

print("Creating sequences...")
X_seq, y_seq = create_sequences(X_scaled, y_scaled)
print("Sequences shape:", X_seq.shape)

# Chronological split (80% train, 20% test)
split = int(len(X_seq) * 0.8)
X_train = X_seq[:split]
X_test = X_seq[split:]
y_train = y_seq[:split]
y_test = y_seq[split:]

# ===============================
# MODEL BUILDER & TRAINING
# ===============================
print("Building GRU architecture...")
model = Sequential([
    GRU(64, return_sequences=True, input_shape=(TIME_STEPS, X_train.shape[2])),
    BatchNormalization(),
    Dropout(0.2),
    GRU(32),
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

print("Training GRU model...")
model.fit(
    X_train,
    y_train,
    epochs=20,
    batch_size=64,
    validation_split=0.2,
    callbacks=[early_stop],
    verbose=1
)

# ===============================
# EVALUATION
# ===============================
print("Evaluating model...")
pred_scaled = model.predict(X_test)
pred = y_scaler.inverse_transform(pred_scaled)
actual = y_scaler.inverse_transform(y_test)

temp_mae = mean_absolute_error(actual[:, 0], pred[:, 0])
temp_r2 = r2_score(actual[:, 0], pred[:, 0])
press_mae = mean_absolute_error(actual[:, 1], pred[:, 1])
press_r2 = r2_score(actual[:, 1], pred[:, 1])
overall_rmse = np.sqrt(mean_squared_error(actual, pred))
overall_r2 = r2_score(actual, pred)

print("\nGRU PERFORMANCE SUMMARY:")
print("Temperature MAE:", temp_mae)
print("Temperature R2 Score:", temp_r2)
print("Pressure MAE:", press_mae)
print("Pressure R2 Score:", press_r2)
print("Overall RMSE:", overall_rmse)
print("Overall R2 Score (average):", overall_r2)
print("Accuracy:", round(overall_r2 * 100, 2), "%")

# ===============================
# SAVE MODEL & SCALERS
# ===============================
model.save(os.path.join(BASE_DIR, "best_gru_weather_model.keras"))
joblib.dump(X_scaler, os.path.join(BASE_DIR, "X_scaler.pkl"))
joblib.dump(y_scaler, os.path.join(BASE_DIR, "y_scaler.pkl"))
joblib.dump(list(X.columns), os.path.join(BASE_DIR, "gru_feature_columns.pkl"))

print("Tuned GRU Saved successfully in:", BASE_DIR)