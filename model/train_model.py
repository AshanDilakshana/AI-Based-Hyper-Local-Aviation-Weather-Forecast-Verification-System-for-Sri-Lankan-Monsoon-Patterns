import pandas as pd
import numpy as np
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

input_path = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")

df = pd.read_csv(input_path)

# Remove datetime because ML model cannot train directly with datetime text
drop_cols = [
    "datetime",
    "target_temperature",
    "target_humidity",
    "target_pressure"
]

X = df.drop(columns=drop_cols)

y = df[[
    "target_temperature",
    "target_humidity",
    "target_pressure"
]]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = MultiOutputRegressor(
    RandomForestRegressor(
        n_estimators=300,
        max_depth=15,
        random_state=42
    )
)

model.fit(X_train_scaled, y_train)

y_pred = model.predict(X_test_scaled)

print("Temperature MAE:", mean_absolute_error(y_test["target_temperature"], y_pred[:, 0]))
print("Humidity MAE:", mean_absolute_error(y_test["target_humidity"], y_pred[:, 1]))
print("Pressure MAE:", mean_absolute_error(y_test["target_pressure"], y_pred[:, 2]))

print("Overall RMSE:", np.sqrt(mean_squared_error(y_test, y_pred)))
print("Overall R2 Score:", r2_score(y_test, y_pred))

joblib.dump(model, os.path.join(PROJECT_DIR, "model", "weather_model.pkl"))
joblib.dump(scaler, os.path.join(PROJECT_DIR, "model", "scaler.pkl"))
joblib.dump(list(X.columns), os.path.join(PROJECT_DIR, "model", "feature_columns.pkl"))

print("✅ Model trained & saved successfully!")
print("Features used:", list(X.columns))