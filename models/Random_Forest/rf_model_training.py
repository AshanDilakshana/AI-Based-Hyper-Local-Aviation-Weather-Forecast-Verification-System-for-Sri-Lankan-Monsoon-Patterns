import pandas as pd
import joblib
import os
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Path Logic
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Adjusted to go UP from models/Random_Forest to reach the root 'data' folder
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR)) 
DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'advanced_multi_data.csv')

def train_rf_model():
    print(f"Researcher: P.K.V.K. Jayathilaka")
    
    if not os.path.exists(DATA_PATH):
        print(f"Error: {DATA_PATH} not found.")
        return

    df = pd.read_csv(DATA_PATH)
    
    # DEBUG: See what columns actually exist
    print(f"Columns found in CSV: {df.columns.tolist()}")

    features = ['QNH (hPa)', 'RH(%)', 'Dry tem(0C)', 'Dew point(0C)', 
                'stability_index', 'hour', 'qnh_momentum', 'rh_momentum']
    targets = ['target_qnh', 'target_rh']
    
    try:
        X = df[features]
        y = df[targets]
    except KeyError as e:
        print(f"\n❌ FAILED: Missing columns in CSV: {e}")
        print("FIX: Run the updated advanced_preprocess.py script first!")
        return

    # Splitting data (80% Training, 20% Testing)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    print("Training Multi-Target Random Forest...")
    # Using 200 trees with a max depth of 12 for high accuracy
    rf = RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42)
    model = MultiOutputRegressor(rf)
    model.fit(X_train, y_train)

    # Saving model and assets
    joblib.dump(model, os.path.join(SCRIPT_DIR, 'rf_model.pkl'))
    joblib.dump((X_test, y_test, features), os.path.join(SCRIPT_DIR, 'rf_test_assets.pkl'))

    # --- ACCURACY CALCULATION SECTION ---
    preds = model.predict(X_test)

    # QNH Metrics (Index 0)
    qnh_r2 = r2_score(y_test.iloc[:, 0], preds[:, 0])
    qnh_mae = mean_absolute_error(y_test.iloc[:, 0], preds[:, 0])
    qnh_rmse = np.sqrt(mean_squared_error(y_test.iloc[:, 0], preds[:, 0]))

    # RH Metrics (Index 1)
    rh_r2 = r2_score(y_test.iloc[:, 1], preds[:, 1])
    rh_mae = mean_absolute_error(y_test.iloc[:, 1], preds[:, 1])
    rh_rmse = np.sqrt(mean_squared_error(y_test.iloc[:, 1], preds[:, 1]))

    # --- DISPLAY FINAL REPORT ---
    print("\n" + "="*55)
    print(f"       AI MODEL ACCURACY REPORT - BIA METAR")
    print(f"       Researcher: P.K.V.K. Jayathilaka")
    print("="*55)
    
    print(f"TARGET 1: QNH (Atmospheric Pressure)")
    print(f"  - R2 Score (Accuracy) : {qnh_r2:.4f}")
    print(f"  - Mean Absolute Error : {qnh_mae:.4f} hPa")
    print(f"  - Root Mean Sq. Error : {qnh_rmse:.4f} hPa")
    
    print("-" * 55)
    
    print(f"TARGET 2: RH (Relative Humidity)")
    print(f"  - R2 Score (Accuracy) : {rh_r2:.4f}")
    print(f"  - Mean Absolute Error : {rh_mae:.4f} %")
    print(f"  - Root Mean Sq. Error : {rh_rmse:.4f} %")
    
    print("="*55)
    print("Model assets saved. You can now run verification/importance plots.\n")

if __name__ == "__main__":
    train_rf_model()