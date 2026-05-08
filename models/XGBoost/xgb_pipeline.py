import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
from sklearn.model_selection import train_test_split
from XGBoost import XGBRegressor
from sklearn.metrics import mean_squared_error, r2_score

# Configuration
DATA_PATH = '../../data/processed_features.csv'
MODEL_DIR = './'

def run_xgb_pipeline():
    # 1. Load Data
    df = pd.read_csv(DATA_PATH)
    features_to_drop = ['target_future_qnh_drop', 'timestamp']
    X = df.drop(columns=[col for col in features_to_drop if col in df.columns])
    y = df['target_future_qnh_drop']

    # 2. Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

    # 3. Train XGBoost
    print("Training XGBoost Regressor...")
    model = XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    # 4. Save Model
    joblib.dump(model, os.path.join(MODEL_DIR, 'xgb_model.pkl'))

    # 5. Verification & Metrics
    predictions = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)
    
    verification_df = pd.DataFrame({'Actual': y_test.values, 'Predicted': predictions})
    verification_df.to_csv(os.path.join(MODEL_DIR, 'verification_xgb.csv'), index=False)
    print(f"XGBoost RMSE: {rmse:.4f}, R2: {r2:.4f}")

    # 6. Feature Importance
    importance_df = pd.DataFrame({
        'Feature': X.columns,
        'Importance': model.feature_importances_
    }).sort_values(by='Importance', ascending=False)
    importance_df.to_csv(os.path.join(MODEL_DIR, 'importance_xgb.csv'), index=False)

    # 7. Save Plot
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=importance_df, palette='magma')
    plt.title('XGBoost Feature Importance - SIM Stability')
    plt.tight_layout()
    plt.savefig(os.path.join(MODEL_DIR, 'importance_plot_xgb.png'))

if __name__ == "__main__":
    run_xgb_pipeline()