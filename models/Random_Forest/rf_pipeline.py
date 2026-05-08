import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Define paths
DATA_PATH = '../../data/processed_features.csv'
MODEL_DIR = './'

def run_model_pipeline():
    # 1. Load Processed Data
    df = pd.read_csv(DATA_PATH)
    
    # Features (X) and Target (y)
    # Exclude target and non-predictive columns (like timestamp)
    features_to_drop = ['target_future_qnh_drop', 'timestamp']
    X = df.drop(columns=[col for col in features_to_drop if col in df.columns])
    y = df['target_future_qnh_drop']
    
    # 2. Train-Test Split (80% Train, 20% Test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False) # shuffle=False for time-series
    
    # 3. Initialize and Train Model (Random Forest)
    print("Training Random Forest Model...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # 4. Save the trained model
    joblib.dump(model, os.path.join(MODEL_DIR, 'random_forest_model.pkl'))
    print("Model saved successfully.")
    
    # 5. Testing and Verification
    predictions = model.predict(X_test)
    
    # Calculate metrics
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    print(f"Model RMSE: {rmse:.4f}")
    
    # Save Actual vs Predicted Verification File
    verification_df = pd.DataFrame({
        'Actual_QNH_Drop': y_test.values,
        'Predicted_QNH_Drop': predictions
    })
    verification_df.to_csv(os.path.join(MODEL_DIR, 'verification_actual_vs_predicted.csv'), index=False)
    print("Verification file saved.")
    
    # 6. Feature Importance Extraction
    importances = model.feature_importances_
    feature_names = X.columns
    
    # Create Feature Importance DataFrame
    importance_df = pd.DataFrame({
        'Feature': feature_names,
        'Importance': importances
    }).sort_values(by='Importance', ascending=False)
    
    # Save Importance DataFrame to CSV
    importance_df.to_csv(os.path.join(MODEL_DIR, 'feature_importance.csv'), index=False)
    
    # 7. Plot Feature Importance and Save as Image
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=importance_df, palette='viridis')
    plt.title('Feature Importance for QNH Stability Prediction (Random Forest)')
    plt.xlabel('Relative Importance')
    plt.ylabel('Features')
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(os.path.join(MODEL_DIR, 'feature_importance_plot.png'))
    print("Feature importance plot saved.")

if __name__ == "__main__":
    run_model_pipeline()