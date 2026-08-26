import os
import sys
import sqlite3
import pandas as pd
import pickle
from sklearn.metrics import accuracy_score, mean_absolute_error

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from Models.cloud_visibility_models.xgboost_model import train_for_mlops

def get_all_historical_data(db_path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM weather_data", conn)
    conn.close()
    return df

def run_cloud_visibility_retraining():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, '../../'))
    db_path = os.path.abspath(os.path.join(project_root, 'weather_data.db'))
    model_dir = os.path.join(project_root, 'Models', 'cloud_visibility_models')
    
    print("[INFO] Starting MLOps Retraining for Cloud & Visibility models...")
    
    # 1. Fetch Data
    try:
        df = get_all_historical_data(db_path)
        if len(df) < 100:
            return False, "Not enough data to retrain (<100 rows)."
    except Exception as e:
        return False, f"Failed to fetch data from DB: {e}"

    # 2. Train New Models
    try:
        (new_cloud_model, new_vis_model, new_cloud_acc, new_vis_mae, 
         cloud_mapping, vis_mapping, 
         X_test_c, y_test_c, X_test_v, y_test_v) = train_for_mlops(df)
        print(f"[INFO] New Model Trained - Cloud Acc: {new_cloud_acc:.4f}, Vis MAE: {new_vis_mae:.4f}")
    except Exception as e:
        return False, f"Training failed: {e}"

    # 3. Evaluate Existing Models (if any)
    cloud_model_path = os.path.join(model_dir, 'xgb_cloud_model.pkl')
    vis_model_path = os.path.join(model_dir, 'xgb_visibility_model.pkl')
    
    old_cloud_acc = 0.0
    old_vis_mae = float('inf')
    
    if os.path.exists(cloud_model_path) and os.path.exists(vis_model_path):
        try:
            with open(cloud_model_path, 'rb') as f:
                old_cloud_bundle = pickle.load(f)
                old_cloud_model = old_cloud_bundle['model']
            
            with open(vis_model_path, 'rb') as f:
                old_vis_bundle = pickle.load(f)
                old_vis_model = old_vis_bundle['model']
            
            # Evaluate old models on new test set
            old_c_preds = old_cloud_model.predict(X_test_c)
            old_cloud_acc = accuracy_score(y_test_c, old_c_preds)
            
            old_v_preds = old_vis_model.predict(X_test_v)
            old_vis_mae = mean_absolute_error(y_test_v, old_v_preds)
            print(f"[INFO] Old Model Evaluated - Cloud Acc: {old_cloud_acc:.4f}, Vis MAE: {old_vis_mae:.4f}")
        except Exception as e:
            print(f"[WARNING] Failed to evaluate old models: {e}. Assuming new model is better.")

    # 4. Compare and Replace
    if (new_cloud_acc >= old_cloud_acc) and (new_vis_mae <= old_vis_mae):
        print("[SUCCESS] New models perform equal or better! Deploying...")
        
        # Backup old models
        if os.path.exists(cloud_model_path):
            os.replace(cloud_model_path, cloud_model_path.replace('.pkl', '_backup.pkl'))
        if os.path.exists(vis_model_path):
            os.replace(vis_model_path, vis_model_path.replace('.pkl', '_backup.pkl'))
            
        # Save new models
        with open(cloud_model_path, 'wb') as f:
            pickle.dump({'model': new_cloud_model, 'mapping': cloud_mapping}, f)
        with open(vis_model_path, 'wb') as f:
            pickle.dump({'model': new_vis_model, 'mapping': vis_mapping}, f)
            
        return True, "New models deployed successfully."
    else:
        print("[INFO] New models did not improve on old models. Retaining existing models.")
        return False, "Models did not improve."

if __name__ == "__main__":
    success, msg = run_cloud_visibility_retraining()
    print(f"Retraining Result: {msg}")
