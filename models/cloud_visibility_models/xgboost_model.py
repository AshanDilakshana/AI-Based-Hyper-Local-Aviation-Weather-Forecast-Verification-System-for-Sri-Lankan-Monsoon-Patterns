import os
import pickle
import sqlite3
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, accuracy_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor, XGBClassifier

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../'))
db_path = os.path.abspath(os.path.join(project_root, '../weather_data.db'))

def clean_cloud(text):
    text = str(text).upper()
    if any(x in text for x in ['BKN', 'OVC']): return 'CLOUDY'
    if any(x in text for x in ['SCT', 'FEW']): return 'PARTLY_CLOUDY'
    if any(x in text for x in ['NSC', 'SKC', 'CLR', 'NIL']): return 'CLEAR'
    return 'OTHER'

def process_data(df):
    # Calculate derived features
    df['Hour'] = pd.to_datetime(df['timestamp_utc'], format='mixed', utc=True).dt.hour
    df['Dew_Point_Depression'] = df['dry_temp_c'] - df['dew_point_c']
    df['Temp_RH'] = df['dry_temp_c'] * df['rh_percent']
    df['Wind_RH'] = df['wind_speed_kts'] * df['rh_percent']
    df['Pressure_Wind'] = df['qnh_hpa'] * df['wind_speed_kts']
    df['RH_Squared'] = df['rh_percent'] ** 2

    # Encode weather
    df['Weather_Encoded'] = df['weather'].astype('category').cat.codes
    df['Cloud_Cleaned'] = df['clouds'].apply(clean_cloud)

    # Rename to match original feature list
    df.rename(columns={
        'month': 'Month',
        'wind_dir': 'Wind Dir.',
        'wind_speed_kts': 'Wind speed(Kts)',
        'dry_temp_c': 'Dry tem(0C)',
        'dew_point_c': 'Dew point(0C)',
        'rh_percent': 'RH(%)',
        'qnh_hpa': 'QNH (hPa)',
        'visibility': 'Visibility_Cleaned'
    }, inplace=True)
    
    # Cast visibility to string category matching preprocessing
    df['Visibility_Cleaned'] = df['Visibility_Cleaned'].astype(str)

    features = [
        'Month', 'Hour', 'Wind Dir.', 'Wind speed(Kts)', 'Dry tem(0C)', 'Dew point(0C)', 
        'RH(%)', 'QNH (hPa)', 'Dew_Point_Depression', 'Temp_RH', 'Wind_RH', 
        'Pressure_Wind', 'RH_Squared', 'Weather_Encoded'
    ]

    df = df.dropna(subset=features + ['Cloud_Cleaned', 'Visibility_Cleaned'])

    # Ordinal mapping for classifications
    df['Cloud_Code'] = df['Cloud_Cleaned'].astype('category').cat.codes
    cloud_mapping = dict(enumerate(df['Cloud_Cleaned'].astype('category').cat.categories))

    # Visibility needs ordinal mapping so we can predict the category index using Regressor
    # To keep regression meaningful, categories should ideally be sorted by numeric value
    unique_vis = sorted(df['Visibility_Cleaned'].unique(), key=lambda x: float(x) if x.replace('.','',1).isdigit() else 0)
    vis_cat = pd.Categorical(df['Visibility_Cleaned'], categories=unique_vis, ordered=True)
    df['Vis_Code'] = vis_cat.codes
    vis_mapping = dict(enumerate(vis_cat.categories))

    return df, features, cloud_mapping, vis_mapping

def train_for_mlops(df):
    df, features, cloud_mapping, vis_mapping = process_data(df)
    
    X = df[features]
    y_cloud = df['Cloud_Code']
    y_vis = df['Vis_Code']
    
    X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, y_cloud, test_size=0.2, random_state=42)
    X_train_v, X_test_v, y_train_v, y_test_v = train_test_split(X, y_vis, test_size=0.2, random_state=42)

    # Cloud Classifier
    cloud_model = XGBClassifier(
        n_estimators=500, max_depth=12, learning_rate=0.1,
        tree_method='hist', random_state=42, n_jobs=-1
    )
    cloud_model.fit(X_train_c, y_train_c)

    # Visibility Regressor
    vis_model = XGBRegressor(
        n_estimators=500, max_depth=7, learning_rate=0.04,
        subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1
    )
    vis_model.fit(X_train_v, y_train_v)

    c_preds = cloud_model.predict(X_test_c)
    v_preds = vis_model.predict(X_test_v)

    cloud_acc = accuracy_score(y_test_c, c_preds)
    vis_mae = mean_absolute_error(y_test_v, v_preds)
    
    return cloud_model, vis_model, cloud_acc, vis_mae, cloud_mapping, vis_mapping, X_test_c, y_test_c, X_test_v, y_test_v

if __name__ == "__main__":
    print(f"[INFO] XGBoost Script: Loading dataset from DB {db_path}...")
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM weather_data", conn)
    conn.close()

    print("\n[TRAINING] Optimizing and Training XGBoost Models (Cloud + Visibility)...")
    cloud_model, vis_model, cloud_acc, vis_mae, cloud_mapping, vis_mapping, _, _, _, _ = train_for_mlops(df)

    print(f"\n[RESULTS] XGBoost Models:")
    print(f"  -> Cloud Classification Accuracy: {cloud_acc * 100:.2f}%")
    print(f"  -> Visibility Mean Absolute Error (MAE): {vis_mae:.4f}")

    # Save to the SAME cloud_visibility_models folder
    save_path = script_dir
    os.makedirs(save_path, exist_ok=True)

    cloud_bundle = {
        'model': cloud_model,
        'mapping': cloud_mapping
    }
    vis_bundle = {
        'model': vis_model,
        'mapping': vis_mapping
    }
    
    import shutil
    from datetime import datetime
    
    def log_retraining_to_db(db_path, model_name, old_metric, new_metric, status, timestamp):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_retraining_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    model_name TEXT,
                    old_mae REAL,
                    new_mae REAL,
                    status TEXT
                )
            ''')
            cursor.execute('''
                INSERT INTO model_retraining_logs (timestamp, model_name, old_mae, new_mae, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, model_name, old_metric, new_metric, status))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Failed to log retraining to database: {e}")
            
    # Cloud Model Promotion (Metric: Accuracy, Higher is better)
    cloud_model_path = os.path.join(save_path, 'xgb_cloud_model.pkl')
    cloud_backup_path = os.path.join(save_path, 'xgb_cloud_model_backup.pkl')
    cloud_status = "Promoted (First Time)"
    old_cloud_acc = None
    
    if os.path.exists(cloud_model_path):
        print("\nExisting Cloud model found. Evaluating...")
        try:
            with open(cloud_model_path, "rb") as f:
                old_cloud_bundle = pickle.load(f)
            old_cloud_model = old_cloud_bundle['model']
            
            old_c_preds = old_cloud_model.predict(X_test_c)
            old_cloud_acc = accuracy_score(y_test_c, old_c_preds)
            print(f"Old Cloud Model Accuracy: {old_cloud_acc * 100:.2f}%")
            
            if cloud_acc > old_cloud_acc:
                print("New Cloud model is BETTER. Promoting and backing up old model...")
                shutil.copy2(cloud_model_path, cloud_backup_path)
                with open(cloud_model_path, 'wb') as f:
                    pickle.dump(cloud_bundle, f)
                cloud_status = "Promoted (Better Accuracy)"
            else:
                print("New Cloud model is WORSE or EQUAL. Discarding...")
                cloud_status = "Discarded (Worse Accuracy)"
        except Exception as e:
            print(f"Error evaluating old Cloud model: {e}. Overwriting...")
            if os.path.exists(cloud_model_path): shutil.copy2(cloud_model_path, cloud_backup_path)
            with open(cloud_model_path, 'wb') as f:
                pickle.dump(cloud_bundle, f)
            cloud_status = "Promoted (Old Model Corrupted)"
    else:
        with open(cloud_model_path, 'wb') as f:
            pickle.dump(cloud_bundle, f)
            
    # Visibility Model Promotion (Metric: MAE, Lower is better)
    vis_model_path = os.path.join(save_path, 'xgb_visibility_model.pkl')
    vis_backup_path = os.path.join(save_path, 'xgb_visibility_model_backup.pkl')
    vis_status = "Promoted (First Time)"
    old_vis_mae = None
    
    if os.path.exists(vis_model_path):
        print("\nExisting Visibility model found. Evaluating...")
        try:
            with open(vis_model_path, "rb") as f:
                old_vis_bundle = pickle.load(f)
            old_vis_model = old_vis_bundle['model']
            
            old_v_preds = old_vis_model.predict(X_test_v)
            old_vis_mae = mean_absolute_error(y_test_v, old_v_preds)
            print(f"Old Visibility Model MAE: {old_vis_mae:.4f}")
            
            if vis_mae < old_vis_mae:
                print("New Visibility model is BETTER. Promoting and backing up old model...")
                shutil.copy2(vis_model_path, vis_backup_path)
                with open(vis_model_path, 'wb') as f:
                    pickle.dump(vis_bundle, f)
                vis_status = "Promoted (Better MAE)"
            else:
                print("New Visibility model is WORSE or EQUAL. Discarding...")
                vis_status = "Discarded (Worse MAE)"
        except Exception as e:
            print(f"Error evaluating old Visibility model: {e}. Overwriting...")
            if os.path.exists(vis_model_path): shutil.copy2(vis_model_path, vis_backup_path)
            with open(vis_model_path, 'wb') as f:
                pickle.dump(vis_bundle, f)
            vis_status = "Promoted (Old Model Corrupted)"
    else:
        with open(vis_model_path, 'wb') as f:
            pickle.dump(vis_bundle, f)
            
    # Database Logging
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_retraining_to_db(db_path, "Cloud_XGBoost", old_cloud_acc, cloud_acc, cloud_status, timestamp)
    log_retraining_to_db(db_path, "Visibility_XGBoost", old_vis_mae, vis_mae, vis_status, timestamp)

    print(f"\n[SUCCESS] MLOps Auto-Retraining completed for Cloud & Visibility models!")
