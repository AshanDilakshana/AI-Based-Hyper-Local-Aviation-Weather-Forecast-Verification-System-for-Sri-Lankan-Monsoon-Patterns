import pandas as pd
import joblib
import os
import numpy as np
import lightgbm as lgb
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Path Logic
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR)) 
DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'advanced_multi_data.csv')

def train_lgbm_model():
    print(f"Researcher: P.K.V.K. Jayathilaka")
    if not os.path.exists(DATA_PATH):
        print("Error: Data not found.")
        return

    df = pd.read_csv(DATA_PATH)
    features = ['QNH (hPa)', 'RH(%)', 'Dry tem(0C)', 'Dew point(0C)', 
                'stability_index', 'hour', 'qnh_momentum', 'rh_momentum']
    targets = ['target_qnh', 'target_rh']
    
    X = df[features]
    y = df[targets]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    print("Training Multi-Target LightGBM Model...")
    # Parameters optimized for weather variability
    lgbm = lgb.LGBMRegressor(n_estimators=1000, learning_rate=0.01, num_leaves=31, random_state=42)
    model = MultiOutputRegressor(lgbm)
    model.fit(X_train, y_train)

    # Save
    joblib.dump(model, os.path.join(SCRIPT_DIR, 'lgbm_model.pkl'))
    joblib.dump((X_test, y_test, features), os.path.join(SCRIPT_DIR, 'lgbm_test_assets.pkl'))

    # Accuracy Results
    preds = model.predict(X_test)
    q_r2, r_r2 = r2_score(y_test.iloc[:,0], preds[:,0]), r2_score(y_test.iloc[:,1], preds[:,1])
    q_mae = mean_absolute_error(y_test.iloc[:,0], preds[:,0])
    r_mae = mean_absolute_error(y_test.iloc[:,1], preds[:,1])

    print("\n" + "="*55)
    print(f"       ACCURACY REPORT - LIGHTGBM")
    print("="*55)
    print(f"QNH Accuracy (R2): {q_r2:.4f} | MAE: {q_mae:.4f}")
    print(f"RH  Accuracy (R2): {r_r2:.4f} | MAE: {r_mae:.4f}")
    print("="*55)

if __name__ == "__main__":
    train_lgbm_model()