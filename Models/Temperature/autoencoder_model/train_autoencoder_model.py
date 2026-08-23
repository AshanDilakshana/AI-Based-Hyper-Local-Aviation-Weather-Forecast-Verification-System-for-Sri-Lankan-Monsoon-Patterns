import pandas as pd
import numpy as np
import joblib
import os

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))

input_path = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")

print("Dataset Path:", input_path)
if not os.path.exists(input_path):
    raise FileNotFoundError(f"Dataset not found: {input_path}")

df = pd.read_csv(input_path)

drop_cols = [
    "datetime",
    "future_time",
    "target_temperature",
    "target_humidity",
    "target_pressure"
]

X = df.drop(columns=drop_cols, errors="ignore")
y = df[[
    "target_temperature",
    "target_pressure"
]]

X = X.select_dtypes(include=[np.number])
X = X.fillna(X.mean())
y = y.fillna(y.mean())

x_scaler = StandardScaler()
y_scaler = StandardScaler()

X_scaled = x_scaler.fit_transform(X)
y_scaled = y_scaler.fit_transform(y)

split_index = int(len(X_scaled) * 0.8)

X_train = X_scaled[:split_index]
X_test = X_scaled[split_index:]

y_train = y_scaled[:split_index]
y_test = y_scaled[split_index:]

input_dim = X_train.shape[1]

# Encoder
input_layer = Input(shape=(input_dim,))
encoded = Dense(64, activation="relu")(input_layer)
encoded = Dropout(0.2)(encoded)
encoded = Dense(32, activation="relu")(encoded)
encoded = Dense(16, activation="relu")(encoded)

# Decoder
decoded = Dense(32, activation="relu")(encoded)
decoded = Dropout(0.2)(decoded)
decoded = Dense(64, activation="relu")(decoded)

output_layer = Dense(2)(decoded)

model = Model(inputs=input_layer, outputs=output_layer)

model.compile(
    optimizer="adam",
    loss="mse",
    metrics=["mae"]
)

early_stop = EarlyStopping(
    monitor="val_loss",
    patience=10,
    restore_best_weights=True
)

print("Training Autoencoder model...")
history = model.fit(
    X_train,
    y_train,
    epochs=100,
    batch_size=32,
    validation_split=0.2,
    callbacks=[early_stop],
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

print("\nAUTOENCODER MODEL PERFORMANCE:")
print("Temperature MAE:", temp_mae)
print("Temperature R2 Score:", temp_r2)
print("Pressure MAE:", pressure_mae)
print("Pressure R2 Score:", pressure_r2)
print("Overall RMSE:", overall_rmse)
print("Overall R2 Score (average):", overall_r2)
print("Accuracy:", round(overall_r2 * 100, 2), "%")

# Save outputs
model.save(os.path.join(BASE_DIR, "autoencoder_weather_model.keras"))
joblib.dump(x_scaler, os.path.join(BASE_DIR, "autoencoder_x_scaler.pkl"))
joblib.dump(y_scaler, os.path.join(BASE_DIR, "autoencoder_y_scaler.pkl"))
joblib.dump(list(X.columns), os.path.join(BASE_DIR, "autoencoder_feature_columns.pkl"))

print("\nAutoencoder Model trained & saved successfully in:", BASE_DIR)