import os
import pickle

import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../'))
FEATURES_CSV = os.path.join(project_root, 'data', 'aviation_weather_features.csv')

CLOUD_MODEL_PATH = os.path.abspath(os.path.join(script_dir, '../saved_models', 'xgb_cloud_model.pkl'))
VIS_MODEL_PATH = os.path.abspath(os.path.join(script_dir, '../saved_models', 'xgb_visibility_model.pkl'))

import numpy as np

print("[INFO] Loading Optimized AI Models from saved_models/...")
with open(CLOUD_MODEL_PATH, 'rb') as f:
    cloud_bundle = pickle.load(f)
cloud_model = cloud_bundle['model']
cloud_mapping = cloud_bundle['mapping']

with open(VIS_MODEL_PATH, 'rb') as f:
    vis_bundle = pickle.load(f)
vis_model = vis_bundle['model']
vis_mapping = vis_bundle['mapping']

df = pd.read_csv(FEATURES_CSV, low_memory=False)

features = [
    'Month', 'Hour', 'Wind Dir.', 'Wind speed(Kts)', 'Dry tem(0C)', 'Dew point(0C)', 
    'RH(%)', 'QNH (hPa)', 'Dew_Point_Depression', 'Temp_RH', 'Wind_RH', 
    'Pressure_Wind', 'RH_Squared', 'Weather_Encoded'
]
df = df.dropna(subset=features + ['Clouds', 'Visibility'])

X = df[features]

c_raw = cloud_model.predict(X)
c_indices = np.clip(np.round(c_raw), 0, len(cloud_mapping) - 1).astype(int)

v_raw = vis_model.predict(X)
v_indices = np.clip(np.round(v_raw), 0, len(vis_mapping) - 1).astype(int)

print("\n" + "="*115)
print("             BIA AVIATION WEATHER - HIGH ACCURACY FORECAST VERIFICATION SYSTEM")
print("="*115)
print(f"{'Row':<5} | {'Actual Vis':<10} | {'Pred Vis':<10} | {'Vis Status':<12} | {'Actual Cloud':<15} | {'Pred Cloud':<12}")
print("-"*115)

# Verify across the whole dataset to get the real system joint accuracy
total_rows = len(df)
display_rows = min(20, total_rows)
joint_match_count = 0

for i in range(total_rows):
    act_vis = pd.to_numeric(df['Visibility'].iloc[i], errors='coerce')
    if pd.isna(act_vis):
        act_vis = 9999
    pred_vis = int(vis_mapping[v_indices[i]])
    act_cloud = str(df['Clouds'].iloc[i]).upper()
    pred_cloud_text = str(cloud_mapping[c_indices[i]])
    
    # 1. Aviation Rule for Visibility (Allowing standard operational margin)
    vis_ok = abs(act_vis - pred_vis) <= 1500 or (act_vis >= 9000 and pred_vis >= 8500)
    
    # 2. Meteorological Rule for Clouds (Matching the Core Cloud Category)
    cloud_ok = (pred_cloud_text in act_cloud) or (any(x in act_cloud for x in ['SKC', 'CAVOK', 'NSC']) and pred_cloud_text == 'NSC')
    
    # Joint Success: Both must satisfy aviation criteria together
    is_joint_match = vis_ok and cloud_ok
    if is_joint_match:
        joint_match_count += 1
        
    # Only print the first 20 rows to keep terminal clean
    if i < display_rows:
        vis_status = "[MATCH]" if is_joint_match else "[MISMATCH]"
        print(f"{i+1:<5} | {int(act_vis):<10} | {pred_vis:<10} | {vis_status:<12} | {act_cloud:<15} | {pred_cloud_text:<12}")

# Calculate the actual Research Verified Accuracy
final_system_accuracy = (joint_match_count / total_rows) * 100

print("="*115)
print(f"[SUCCESS] OVERALL SYSTEM VERIFIED ACCURACY (Visibility & Clouds Jointly): {final_system_accuracy:.2f}%")
print("===================================================================================================\n")