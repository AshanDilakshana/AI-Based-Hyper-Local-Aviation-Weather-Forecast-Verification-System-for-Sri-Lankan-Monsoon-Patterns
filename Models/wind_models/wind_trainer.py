import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
import os
import torch

def train_xgboost_model(data_path: str, target_cols: list, output_dir: str, model_filename: str):
    """
    A unified function to train, evaluate, and save an XGBoost model.
    """
    print(f"1. Loading processed data from {data_path}...")
    if not os.path.exists(data_path):
        print(f"Error: Could not find {data_path}. Please run the pipeline first.")
        return

    df = pd.read_csv(data_path)

    # Separate Features (X) and Target (y)
    X = df.drop(columns=target_cols)
    y = df[target_cols]

    print("2. Splitting data into Training and Testing sets (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("3. Running Hyperparameter Tuning (GridSearchCV)...")
    # Using a robust grid for high accuracy
    param_grid = {
        'n_estimators': [300, 500, 1000],
        'max_depth': [5, 7, 9],
        'learning_rate': [0.01, 0.05],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0]
    }

    gpu_device = 'cuda' if torch.cuda.is_available() else 'cpu'
    base_model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42, tree_method='hist', device=gpu_device)
    
    # Use n_jobs=1 when using GPU to prevent CUDA/multiprocessing deadlocks on Windows
    n_jobs = 1 if gpu_device == 'cuda' else -1
    search = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        scoring='neg_mean_absolute_error',
        cv=3,
        verbose=1,
        n_jobs=n_jobs
    )

    search.fit(X_train, y_train)
    best_model = search.best_estimator_
    
    print(f"\n✅ Best Parameters Found: {search.best_params_}")

    print("\n4. Evaluating Model Performance...")
    train_predictions = best_model.predict(X_train)
    train_mae = mean_absolute_error(y_train, train_predictions)
    train_rmse = np.sqrt(mean_squared_error(y_train, train_predictions))
    train_r2 = r2_score(y_train, train_predictions)

    test_predictions = best_model.predict(X_test)
    test_mae = mean_absolute_error(y_test, test_predictions)
    test_rmse = np.sqrt(mean_squared_error(y_test, test_predictions))
    test_r2 = r2_score(y_test, test_predictions)

    print("\n" + "="*45)
    print(f"      MODEL ACCURACY REPORT: {', '.join(target_cols)}")
    print("="*45)
    print("--- TRAINING SET (SEEN DATA) ---")
    print(f"Accuracy (R² Score):            {train_r2 * 100:.2f}%")
    print(f"Mean Absolute Error (MAE):      {train_mae:.2f} Knots")
    print(f"Root Mean Squared Error (RMSE): {train_rmse:.2f} Knots")
    
    print("\n--- TESTING SET (UNSEEN DATA) ---")
    print(f"Accuracy (R² Score):            {test_r2 * 100:.2f}%")
    print(f"Mean Absolute Error (MAE):      {test_mae:.2f} Knots")
    print(f"Root Mean Squared Error (RMSE): {test_rmse:.2f} Knots")
    print("="*45)

    print("\n5. Saving Best Trained Model...")
    os.makedirs(output_dir, exist_ok=True)
    model_save_path = os.path.join(output_dir, model_filename)
    best_model.save_model(model_save_path)
    print(f"✅ Model successfully saved to: {model_save_path}")

def train_for_mlops(df: pd.DataFrame, target_cols: list):
    """
    Trains a model using GridSearchCV and returns the model object and test metrics.
    No file is saved here. MLOps handles saving.
    """
    X = df.drop(columns=target_cols)
    y = df[target_cols]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Optimized grid for MLOps retraining: fast execution on GPU while testing top architectures
    param_grid = {
        'n_estimators': [500, 1000],
        'max_depth': [7, 9],
        'learning_rate': [0.05],
        'subsample': [0.8],
        'colsample_bytree': [0.8]
    }
    gpu_device = 'cuda' if torch.cuda.is_available() else 'cpu'
    base_model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42, tree_method='hist', device=gpu_device)
    
    # In Celery workers and with CUDA, n_jobs must be 1 to prevent multiprocessing deadlocks on Windows
    search = GridSearchCV(base_model, param_grid, scoring='neg_mean_absolute_error', cv=3, n_jobs=1, verbose=1)
    search.fit(X_train, y_train)
    
    best_model = search.best_estimator_
    print(f"[MLOps] Best parameters: {search.best_params_}")
    
    test_predictions = best_model.predict(X_test)
    test_mae = mean_absolute_error(y_test, test_predictions)
    
    return best_model, test_mae, X_test, y_test

def evaluate_old_model(model_path: str, X_test: pd.DataFrame, y_test: pd.Series):
    """
    Evaluates an existing model on the provided test set.
    """
    if not os.path.exists(model_path):
        return None # Old model doesn't exist yet
    
    old_model = xgb.XGBRegressor()
    old_model.load_model(model_path)
    
    # Ensure feature alignment
    features = old_model.feature_names_in_
    X_test_aligned = X_test[features]
    
    predictions = old_model.predict(X_test_aligned)
    try:
        mae = mean_absolute_error(y_test, predictions)
        return mae
    except ValueError:
        print("Shape mismatch between old model predictions and new targets. Returning None.")
        return None
