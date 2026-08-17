import pandas as pd
import numpy as np
import joblib
import os
import sys

# Ensure project modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from Models.weather_pipeline import UnifiedWeatherPipeline

def train_weather_model():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
    
    # Read raw METAR data
    raw_data_path = os.path.join(PROJECT_DIR, "data", "bia_metar_data.xlsx")
    if not os.path.exists(raw_data_path):
        print(f"Error: {raw_data_path} not found.")
        return
        
    df_raw = pd.read_excel(raw_data_path)
    
    print("--- Running Preprocessing & Feature Engineering ---")
    pipeline = UnifiedWeatherPipeline()
    
    df_clean = pipeline.cleaner.clean(df_raw)
    df_features = pipeline.engineer.create_features(df_clean)
    
    # Targets computation
    df_features["future_time"] = df_features["datetime"] + pd.Timedelta(hours=3)
    future_df = df_features[["datetime", "temperature", "pressure", "humidity"]].copy()
    future_df = future_df.rename(columns={
        "datetime": "future_time",
        "temperature": "target_temperature",
        "pressure": "target_pressure",
        "humidity": "target_humidity"
    })
    df_features = df_features.merge(future_df, on="future_time", how="left")
    
    # Drop rows without targets and drop rows with NaNs
    df_features = df_features.dropna(subset=pipeline.targets)
    df_features = df_features.dropna()
    
    # Save the featured dataset to data/featured_northeast_monsoon.csv
    featured_csv_path = os.path.join(PROJECT_DIR, "data", "featured_northeast_monsoon.csv")
    df_features.to_csv(featured_csv_path, index=False)
    print(f"[SUCCESS] Preprocessed and featured dataset saved to: {featured_csv_path}")
    
    # Load for training
    df_train = pd.read_csv(featured_csv_path)
    
    drop_cols = ["datetime", "future_time"] + pipeline.targets
    X = df_train.drop(columns=drop_cols, errors="ignore")
    X = X.select_dtypes(include=[np.number])
    y = df_train[pipeline.targets]
    
    print(f"X shape: {X.shape}, y shape: {y.shape}")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Hyperparameter tuning using GridSearchCV
    rf = RandomForestRegressor(
        random_state=42,
        n_jobs=-1
    )
    model = MultiOutputRegressor(rf)
    
    param_grid = {
        "estimator__n_estimators": [800, 1000, 1200],
        "estimator__max_depth": [20, 25, 30, 35, None],
        "estimator__min_samples_split": [2, 3, 4, 5],
        "estimator__min_samples_leaf": [1, 2, 3],
        "estimator__max_features": [0.7, 0.8, 0.9],
        "estimator__bootstrap": [True]
    }
    
    print("\n--- Starting GridSearchCV hyperparameter tuning (this may take several minutes) ---")
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
    
    print("\n[SUCCESS] Best Parameters Found:")
    print(grid_search.best_params_)
    
    y_pred = best_model.predict(X_test_scaled)
    
    # Evaluation
    temp_mae = mean_absolute_error(y_test["target_temperature"], y_pred[:, 0])
    press_mae = mean_absolute_error(y_test["target_pressure"], y_pred[:, 1])
    humidity_mae = mean_absolute_error(y_test["target_humidity"], y_pred[:, 2])
    overall_r2 = r2_score(y_test, y_pred)
    
    print("\n--- TUNED RANDOM FOREST PERFORMANCE (3-Hour Forecast) ---")
    print(f"Temperature MAE: {temp_mae:.4f} C")
    print(f"Pressure MAE: {press_mae:.4f} hPa")
    print(f"Humidity MAE: {humidity_mae:.4f} %")
    print(f"Overall R2 Score: {overall_r2 * 100:.2f} %")
    
    # Save the models
    joblib.dump(best_model, os.path.join(BASE_DIR, "weather_model.pkl"))
    joblib.dump(scaler, os.path.join(BASE_DIR, "scaler.pkl"))
    joblib.dump(list(X.columns), os.path.join(BASE_DIR, "feature_columns.pkl"))
    
    print("\n[SUCCESS] Tuned weather model and scalers saved successfully!")

if __name__ == "__main__":
    train_weather_model()
