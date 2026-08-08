import pandas as pd
import joblib
import os
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Path Logic
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR)) 
QNH_DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'data_qnh.csv')
RH_DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'data_rh.csv')

def train_separated_models():
    print(f"Researcher: P.K.V.K. Jayathilaka | Training Separated Models")
    
    # ---------------------------------------------------------
    # Train QNH Model
    # ---------------------------------------------------------
    if not os.path.exists(QNH_DATA_PATH):
        print("Error: QNH Data not found.")
        return
        
    df_qnh = pd.read_csv(QNH_DATA_PATH)
    qnh_features = [col for col in df_qnh.columns if col != 'target_qnh']
    
    X_q = df_qnh[qnh_features]
    y_q = df_qnh['target_qnh']
    X_train_q, X_test_q, y_train_q, y_test_q = train_test_split(X_q, y_q, test_size=0.2, shuffle=False)
    
    print("Training LightGBM Model for QNH...")
    lgbm_qnh = lgb.LGBMRegressor(n_estimators=1000, learning_rate=0.01, num_leaves=31, random_state=42)
    lgbm_qnh.fit(X_train_q, y_train_q)
    
    joblib.dump(lgbm_qnh, os.path.join(SCRIPT_DIR, 'lgbm_qnh_model.pkl'))
    joblib.dump((X_test_q, y_test_q, qnh_features), os.path.join(SCRIPT_DIR, 'lgbm_qnh_test_assets.pkl'))
    
    q_preds = lgbm_qnh.predict(X_test_q)
    q_r2 = r2_score(y_test_q, q_preds)
    q_mae = mean_absolute_error(y_test_q, q_preds)

    # ---------------------------------------------------------
    # Train RH Model
    # ---------------------------------------------------------
    if not os.path.exists(RH_DATA_PATH):
        print("Error: RH Data not found.")
        return
        
    df_rh = pd.read_csv(RH_DATA_PATH)
    rh_features = [col for col in df_rh.columns if col != 'target_rh']
    
    X_r = df_rh[rh_features]
    y_r = df_rh['target_rh']
    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X_r, y_r, test_size=0.2, shuffle=False)
    
    print("Training LightGBM Model for RH...")
    lgbm_rh = lgb.LGBMRegressor(n_estimators=1000, learning_rate=0.01, num_leaves=31, random_state=42)
    lgbm_rh.fit(X_train_r, y_train_r)
    
    joblib.dump(lgbm_rh, os.path.join(SCRIPT_DIR, 'lgbm_rh_model.pkl'))
    joblib.dump((X_test_r, y_test_r, rh_features), os.path.join(SCRIPT_DIR, 'lgbm_rh_test_assets.pkl'))
    
    r_preds = lgbm_rh.predict(X_test_r)
    r_r2 = r2_score(y_test_r, r_preds)
    r_mae = mean_absolute_error(y_test_r, r_preds)

    # ---------------------------------------------------------
    # Results
    # ---------------------------------------------------------
    print("\n" + "="*55)
    print(f"       ACCURACY REPORT - SEPARATED LIGHTGBM")
    print("="*55)
    print(f"QNH Accuracy (R2): {q_r2:.4f} | MAE: {q_mae:.4f}")
    print(f"RH  Accuracy (R2): {r_r2:.4f} | MAE: {r_mae:.4f}")
    print("="*55)

if __name__ == "__main__":
    train_separated_models()