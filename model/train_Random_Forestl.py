import pandas as pd
import numpy as np
import joblib
import os

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

input_path = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")
df = pd.read_csv(input_path)

# Columns not used as model inputs
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

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    shuffle=False
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

rf = RandomForestRegressor(
    random_state=42,
    n_jobs=-1
)

model = MultiOutputRegressor(rf)

param_grid = {
    "estimator__n_estimators": [800, 1000, 1200],
    "estimator__max_depth": [18, 22, 25, None],
    "estimator__min_samples_split": [2, 3, 4],
    "estimator__min_samples_leaf": [1, 2],
    "estimator__max_features": [0.8, 0.9, None],
    "estimator__bootstrap": [True]
}

grid_search = GridSearchCV(
    estimator=model,
    param_grid=param_grid,
    scoring="r2",
    cv=3,
    verbose=2,
    n_jobs=-1
)

grid_search.fit(X_train_scaled, y_train)

best_model = grid_search.best_estimator_

print("\n✅ Best Parameters:")
print(grid_search.best_params_)

y_pred = best_model.predict(X_test_scaled)

temp_mae = mean_absolute_error(y_test["target_temperature"], y_pred[:, 0])
pressure_mae = mean_absolute_error(y_test["target_pressure"], y_pred[:, 1])
overall_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
overall_r2 = r2_score(y_test, y_pred)

print("\n📊 TUNED RANDOM FOREST PERFORMANCE")
print("Temperature MAE:", temp_mae)
print("Pressure MAE:", pressure_mae)
print("Overall RMSE:", overall_rmse)
print("Overall R2 Score:", overall_r2)
print("Accuracy:", round(overall_r2 * 100, 2), "%")

joblib.dump(best_model, os.path.join(BASE_DIR, "weather_model.pkl"))
joblib.dump(scaler, os.path.join(BASE_DIR, "scaler.pkl"))
joblib.dump(list(X.columns), os.path.join(BASE_DIR, "feature_columns.pkl"))

print("\n✅ Best tuned model saved successfully!")
print("Saved in:", BASE_DIR)
print("Features used:", list(X.columns))