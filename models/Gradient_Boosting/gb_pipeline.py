import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error

DATA_PATH = '../../data/processed_features.csv'
MODEL_DIR = './'

def run_gb_pipeline():
    # 1. Load Data
    df = pd.read_csv(DATA_PATH)
    X = df.drop(columns=['target_future_qnh_drop', 'timestamp'], errors='ignore')
    y = df['target_future_qnh_drop']

    # 2. Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

    # 3. Train Gradient Boosting
    print("Training Gradient Boosting Regressor...")
    model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 4. Save Model
    joblib.dump(model, os.path.join(MODEL_DIR, 'gb_model.pkl'))

    # 5. Verification
    predictions = model.predict(X_test)
    verification_df = pd.DataFrame({'Actual': y_test.values, 'Predicted': predictions})
    verification_df.to_csv(os.path.join(MODEL_DIR, 'verification_gb.csv'), index=False)

    # 6. Feature Importance
    importance_df = pd.DataFrame({
        'Feature': X.columns,
        'Importance': model.feature_importances_
    }).sort_values(by='Importance', ascending=False)
    importance_df.to_csv(os.path.join(MODEL_DIR, 'importance_gb.csv'), index=False)

    # 7. Plot and Save
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=importance_df, palette='rocket')
    plt.title('Gradient Boosting Feature Importance')
    plt.tight_layout()
    plt.savefig(os.path.join(MODEL_DIR, 'importance_plot_gb.png'))

if __name__ == "__main__":
    run_gb_pipeline()