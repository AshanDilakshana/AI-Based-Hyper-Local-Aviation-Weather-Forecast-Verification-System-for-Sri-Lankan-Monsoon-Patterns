import pandas as pd
import pickle
import os
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error

# Path configuration
BASE_DIR = r'C:\Users\USER\Desktop\Research_IT22619976\AI-Based-Hyper-Local-Aviation-Weather-Forecast-Verification-System-for-Sri-Lankan-Monsoon-Patterns'
DATA_FILE = os.path.join(BASE_DIR, 'data', 'aviation_weather_features.csv')
MODEL_SAVE_PATH = os.path.join(BASE_DIR, 'models', 'models')

def train_maximum_accuracy_model():
    if not os.path.exists(DATA_FILE):
        print("❌ Error: Feature file not found.")
        return

    df = pd.read_csv(DATA_FILE)

    # Features and Target
    feature_cols = ['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']
    X = df[feature_cols]
    y_vis = df['Visibility']

    # Using a smaller test size to give more data for training
    X_train, X_test, y_train, y_test = train_test_split(X, y_vis, test_size=0.1, random_state=42)

    print("⏳ Training Maximum Accuracy Model (Deep Learning Mode)...")
    
    # Deep XGBoost configuration for maximum pattern recognition
    model = XGBRegressor(
        n_estimators=3000,     # Tripled estimators for finer detail
        max_depth=25,          # Deep trees for complex weather patterns
        learning_rate=0.01,    # Slower learning for higher precision
        subsample=0.9,
        colsample_bytree=0.9,
        n_jobs=-1,
        random_state=42,
        tree_method='hist'     # Faster processing for deep trees
    )

    model.fit(X_train, y_train)

    # Evaluation
    preds = model.predict(X_test)
    accuracy_r2 = r2_score(y_test, preds) * 100
    
    print(f"📊 Optimized R2 Accuracy: {accuracy_r2:.2f}%")
    print(f"📊 Mean Absolute Error: {mean_absolute_error(y_test, preds):.2f}m")

    # Save the High-Accuracy model
    with open(os.path.join(MODEL_SAVE_PATH, 'xgboost_visibility.pkl'), 'wb') as f:
        pickle.dump(model, f)

    print(f"🚀 Maximum Accuracy model saved successfully!")

if __name__ == "__main__":
    train_maximum_accuracy_model()