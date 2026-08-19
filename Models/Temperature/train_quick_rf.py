import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error, r2_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))

input_path = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")
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
X = X.replace([np.inf, -np.inf], np.nan)
X = X.fillna(X.mean())

y = y.replace([np.inf, -np.inf], np.nan)
y = y.fillna(y.mean())

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train baseline random forest model quickly
print("Training quick baseline model...")
rf = RandomForestRegressor(
    n_estimators=100,
    max_depth=20,
    random_state=42,
    n_jobs=-1
)
model = MultiOutputRegressor(rf)
model.fit(X_train_scaled, y_train)

y_pred = model.predict(X_test_scaled)
overall_r2 = r2_score(y_test, y_pred)

print("\n--- BASELINE RANDOM FOREST PERFORMANCE ---")
print("Temperature MAE:", mean_absolute_error(y_test["target_temperature"], y_pred[:, 0]))
print("Pressure MAE:", mean_absolute_error(y_test["target_pressure"], y_pred[:, 1]))
print("Overall R2 Score:", overall_r2)

# Save the trained model, scaler and features
joblib.dump(model, os.path.join(BASE_DIR, "weather_model.pkl"))
joblib.dump(scaler, os.path.join(BASE_DIR, "scaler.pkl"))
joblib.dump(list(X.columns), os.path.join(BASE_DIR, "feature_columns.pkl"))

print("\nModel saved successfully!")
