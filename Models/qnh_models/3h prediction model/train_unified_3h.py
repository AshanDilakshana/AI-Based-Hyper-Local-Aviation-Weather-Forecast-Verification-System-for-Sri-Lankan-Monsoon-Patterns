import os
import sys
import joblib
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Add project root to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '../../..'))
sys.path.append(PROJECT_ROOT)

from preprocessing_and_feature_engineering.qnh_prediction_model.unified_pipeline import QNHUnifiedPipeline

def train_qnh_3h_model():
    print("Starting QNH 3H Prediction Model Training...")
    
    db_path = os.path.join(PROJECT_ROOT, 'weather_data.db')
    pipeline = QNHUnifiedPipeline(db_path)
    
    # Get processed data
    try:
        df = pipeline.run_pipeline()
    except Exception as e:
        print(f"Error in pipeline: {e}")
        return

    # Define features and target
    features = pipeline.get_feature_columns(df)
    
    X = df[features]
    y = df['target_qnh_3h']
    
    # Train-test split (time series split: no shuffle)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    print(f"Training Data Shape: {X_train.shape}")
    print(f"Testing Data Shape: {X_test.shape}")
    
    # LightGBM Model
    print("Training LightGBM Regressor...")
    model = lgb.LGBMRegressor(n_estimators=1000, learning_rate=0.01, num_leaves=31, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    preds = model.predict(X_test)
    r2 = r2_score(y_test, preds)
    mae = mean_absolute_error(y_test, preds)
    rmse = mean_squared_error(y_test, preds) ** 0.5
    
    print("\n" + "="*50)
    print("       QNH 3H FORECAST MODEL METRICS")
    print("="*50)
    print(f"R-squared (R2): {r2:.4f}")
    print(f"Mean Absolute Error (MAE): {mae:.4f}")
    print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")
    print("="*50)
    
    # Save Model and Test Assets
    model_path = os.path.join(SCRIPT_DIR, 'qnh_3h_lgbm.pkl')
    assets_path = os.path.join(SCRIPT_DIR, 'qnh_3h_test_assets.pkl')
    
    joblib.dump(model, model_path)
    joblib.dump((X_test, y_test, features), assets_path)
    print(f"Model saved to: {model_path}")

if __name__ == "__main__":
    train_qnh_3h_model()
