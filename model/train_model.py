import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# 1. Load featured data
df = pd.read_csv("data/featured_northeast_monsoon.csv")

# 2. Define inputs (X)
X = df[
    [
        "temperature",
        "humidity",
        "pressure",
        "hour",
        "day",
        "month",
        "temp_lag1",
        "humidity_lag1",
        "pressure_lag1",
        "temp_roll3",
        "humidity_roll3",
        "pressure_roll3",
    ]
]

# 3. Define outputs (y)
y = df[
    [
        "target_temperature",
        "target_humidity",
        "target_pressure",
    ]
]

# 4. Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False
)

# 5. Scaling
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 6. Coupled multi-output model
model = MultiOutputRegressor(
    RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )
)

# 7. Train model
model.fit(X_train_scaled, y_train)

# 8. Predictions
y_pred = model.predict(X_test_scaled)

# 9. Evaluation
print("Temperature MAE:", mean_absolute_error(y_test["target_temperature"], y_pred[:, 0]))
print("Humidity MAE:", mean_absolute_error(y_test["target_humidity"], y_pred[:, 1]))
print("Pressure MAE:", mean_absolute_error(y_test["target_pressure"], y_pred[:, 2]))

print("Overall RMSE:", np.sqrt(mean_squared_error(y_test, y_pred)))
print("Overall R2 Score:", r2_score(y_test, y_pred))

# 10. Save model
joblib.dump(model, "model/weather_model.pkl")
joblib.dump(scaler, "model/scaler.pkl")
joblib.dump(list(X.columns), "model/feature_columns.pkl")

print("\n✅ Model trained & saved successfully!")