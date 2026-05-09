import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder

# --- DYNAMIC PATH SETUP ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'processed_features.csv')
MODEL_DIR = SCRIPT_DIR 

def run_xgb_pipeline():
    print(f"Checking for data at: {DATA_PATH}")
    if not os.path.exists(DATA_PATH):
        print(f"ERROR: File not found at {DATA_PATH}")
        return

    # 1. Load Data with low_memory=False to handle the mixed types
    df = pd.read_csv(DATA_PATH, low_memory=False)
    
    # 2. DATA CLEANING (Fixing the ValueError)
    print("Cleaning data for XGBoost...")
    
    # Define columns that should be numbers but are 'objects'
    numeric_cols = ['Visibility', 'Dry tem(0C)', 'Dew point(0C)', 'Wind speed(Kts)']
    for col in numeric_cols:
        if col in df.columns:
            # errors='coerce' turns text/symbols into NaN, then we fill them
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Define categorical columns to encode as numbers
    categorical_cols = ['METAR /SPECI', 'Wind Dir.', 'Weather', 'Clouds']
    le = LabelEncoder()
    for col in categorical_cols:
        if col in df.columns:
            # Convert to string first to handle any mixed types, then encode
            df[col] = le.fit_transform(df[col].astype(str))

    # Drop non-numeric leftovers (like 'Unnamed' or timestamps)
    df = df.select_dtypes(include=[np.number])
    
    # Handle missing values created during conversion
    df = df.ffill().bfill()

    # 3. Features and Target
    target = 'target_future_qnh_drop'
    if target not in df.columns:
        print(f"Error: {target} not found in numeric columns.")
        return

    X = df.drop(columns=[target])
    y = df[target]

    # 4. Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

    # 5. Train XGBoost
    print("Training XGBoost Regressor...")
    model = XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    # 6. Save Model
    joblib.dump(model, os.path.join(MODEL_DIR, 'xgb_model.pkl'))

    # 7. Metrics
    predictions = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)
    print(f"XGBoost SUCCESS | RMSE: {rmse:.4f}, R2: {r2:.4f}")

    # 8. Feature Importance
    importance_df = pd.DataFrame({'Feature': X.columns, 'Importance': model.feature_importances_}).sort_values(by='Importance', ascending=False)
    importance_df.to_csv(os.path.join(MODEL_DIR, 'importance_xgb.csv'), index=False)

    # 9. Save Plot
    plt.figure(figsize=(10, 8))
    sns.barplot(x='Importance', y='Feature', data=importance_df.head(15), palette='magma')
    plt.title('Top 15 Features - SIM Stability Prediction')
    plt.tight_layout()
    plt.savefig(os.path.join(MODEL_DIR, 'importance_plot_xgb.png'))
    print("Results and plots saved in the XGBoost folder.")

if __name__ == "__main__":
    run_xgb_pipeline()