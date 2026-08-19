import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
MODEL_DIR = os.path.join(PROJECT_DIR, "model")

input_path = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")
df = pd.read_csv(input_path)

drop_cols = ["datetime", "future_time", "target_temperature", "target_humidity", "target_pressure"]
X = df.drop(columns=drop_cols, errors="ignore").select_dtypes(include=[np.number])
X = X.replace([np.inf, -np.inf], np.nan).fillna(X.mean())

y_temp = df["target_temperature"].replace([np.inf, -np.inf], np.nan).fillna(df["target_temperature"].mean())

X_train, X_test, y_train, y_test = train_test_split(X, y_temp, test_size=0.2, shuffle=False)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("Evaluating Random Forest configurations for Temperature...")
configs = [
    {"n_estimators": 50, "max_depth": 10},
    {"n_estimators": 100, "max_depth": 15},
    {"n_estimators": 100, "max_depth": None, "min_samples_split": 5},
]

for config in configs:
    rf = RandomForestRegressor(random_state=42, n_jobs=-1, **config)
    rf.fit(X_train_scaled, y_train)
    preds = rf.predict(X_test_scaled)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    print(f"Config {config}: MAE = {mae:.4f}, R2 = {r2:.4f}")
