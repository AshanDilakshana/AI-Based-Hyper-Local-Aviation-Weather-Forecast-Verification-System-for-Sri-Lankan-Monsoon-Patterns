import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error

def train_for_mlops(df_processed: pd.DataFrame, target_cols: list):
    """
    Trains a MultiOutput RandomForestRegressor model for MLOps.
    """
    X = df_processed.drop(columns=target_cols, errors="ignore")
    X = X.select_dtypes(include=[np.number])
    y = df_processed[target_cols]
    
    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    
    rf = RandomForestRegressor(
        n_estimators=100,
        max_depth=20,
        random_state=42,
        n_jobs=-1
    )
    model = MultiOutputRegressor(rf)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    maes = []
    for i in range(len(target_cols)):
        mae = mean_absolute_error(y_test.iloc[:, i], y_pred[:, i])
        maes.append(mae)
    avg_mae = float(np.mean(maes))
    
    return model, avg_mae, X_test, y_test

def evaluate_old_model(model_path: str, X_test, y_test):
    """
    Loads and evaluates the old model on the new test set.
    """
    if not os.path.exists(model_path):
        return None
    try:
        model = joblib.load(model_path)
        y_pred = model.predict(X_test)
        
        maes = []
        for i in range(y_test.shape[1]):
            mae = mean_absolute_error(y_test.iloc[:, i], y_pred[:, i])
            maes.append(mae)
        return float(np.mean(maes))
    except Exception as e:
        print(f"Error evaluating old model: {e}")
        return None
