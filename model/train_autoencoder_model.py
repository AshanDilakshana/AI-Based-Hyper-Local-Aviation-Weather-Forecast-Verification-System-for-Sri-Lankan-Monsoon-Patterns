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

# ---------------- AUTOENCODER MODEL ----------------

input_layer = Input(shape=(input_dim,))

encoded = Dense(64, activation="relu")(input_layer)
encoded = Dropout(0.2)(encoded)
encoded = Dense(32, activation="relu")(encoded)
encoded = Dense(16, activation="relu")(encoded)

decoded = Dense(32, activation="relu")(encoded)
decoded = Dropout(0.2)(decoded)
decoded = Dense(64, activation="relu")(decoded)

# prediction output: temperature and pressure
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

history = model.fit(
    X_train,
    y_train,
    epochs=100,
    batch_size=16,
    validation_split=0.2,
    callbacks=[early_stop],
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

model.save(os.path.join(BASE_DIR, "autoencoder_weather_model.keras"))

joblib.dump(x_scaler, os.path.join(BASE_DIR, "autoencoder_x_scaler.pkl"))
joblib.dump(y_scaler, os.path.join(BASE_DIR, "autoencoder_y_scaler.pkl"))
joblib.dump(list(X.columns), os.path.join(BASE_DIR, "autoencoder_feature_columns.pkl"))

print("\n✅ Autoencoder Model trained & saved successfully!")
print("Saved in:", BASE_DIR)
print("Features used:", list(X.columns))