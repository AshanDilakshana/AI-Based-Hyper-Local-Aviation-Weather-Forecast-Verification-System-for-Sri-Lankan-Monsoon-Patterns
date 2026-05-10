import pandas as pd
import pickle
import numpy as np
import os

# 1. Handling Dynamic Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../"))

# Paths for models
MODEL_VIS_PATH = os.path.join(BASE_DIR, 'models', 'random_forest_visibility.pkl')
MODEL_CLOUD_PATH = os.path.join(BASE_DIR, 'models', 'random_forest_cloud.pkl')

# Fallback path check
if not os.path.exists(MODEL_VIS_PATH):
    MODEL_VIS_PATH = os.path.join(BASE_DIR, 'random_forest_visibility.pkl')
    MODEL_CLOUD_PATH = os.path.join(BASE_DIR, 'random_forest_cloud.pkl')

# Paths for data files
FEATURES_CSV = os.path.join(BASE_DIR, '../data/aviation_weather_features.csv')
ORIGINAL_EXCEL = os.path.join(BASE_DIR, '../data/BIA_METAR_DATA_(2019_2024).xlsx')

# 2. Load the trained AI models
try:
    with open(MODEL_VIS_PATH, 'rb') as f:
        vis_model = pickle.load(f)
    with open(MODEL_CLOUD_PATH, 'rb') as f:
        cloud_model = pickle.load(f)
    print("✅ AI Models Loaded Successfully!")
except FileNotFoundError:
    print(f"❌ Error: Model files not found at {MODEL_VIS_PATH}")
    exit()

# 3. Load Datasets
try:
    # Load the processed features for AI input
    df_features = pd.read_csv(FEATURES_CSV)
    df_features.columns = df_features.columns.str.strip()
    
    # Load the original Excel to get actual cloud labels before preprocessing
    df_original = pd.read_excel(ORIGINAL_EXCEL)
    df_original.columns = df_original.columns.str.strip()
    
    # Take the top 20 samples from both to ensure they match
    test_sample = df_features.head(20).copy()
    actual_labels = df_original.head(20)['Clouds'].values # Getting original cloud text
    
    # Mapping for AI predictions
    cloud_mapping = {0: 'OVC', 1: 'BKN', 2: 'SCT', 3: 'FEW', 4: 'NSC'}

except Exception as e:
    print(f"❌ Data Loading Error: {e}")
    exit()

# 4. Generate AI Predictions
feature_cols = ['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']
test_sample['Predicted_Visibility'] = vis_model.predict(test_sample[feature_cols])
test_sample['Predicted_Cloud_Idx'] = cloud_model.predict(test_sample[feature_cols])

# 5. Verification Display (Visibility & Clouds)
print("\n" + "="*115)
print("             BIA AVIATION WEATHER - FORECAST VERIFICATION RESULTS (VISIBILITY & CLOUDS)")
print("="*115)
print(f"{'Row':<4} | {'Actual Vis':<10} | {'Pred Vis':<10} | {'Vis Status':<12} | {'Actual Cloud':<15} | {'Pred Cloud':<12}")
print("-" * 115)

for i in range(len(test_sample)):
    # Getting visibility data
    actual_v = int(test_sample.iloc[i]['Visibility'])
    pred_v = int(test_sample.iloc[i]['Predicted_Visibility'])
    
    # Getting cloud data (Actual from Excel, Predicted from AI)
    actual_c = str(actual_labels[i])
    pred_c_idx = int(test_sample.iloc[i]['Predicted_Cloud_Idx'])
    pred_c = cloud_mapping.get(pred_c_idx, "N/A")
    
    # Visibility Match Logic (within 1000m)
    vis_match = "✅ MATCH" if abs(actual_v - pred_v) < 1000 else "❌ MISMATCH"
    
    print(f"{i+1:<4} | {actual_v:<10} | {pred_v:<10} | {vis_match:<12} | {actual_c:<15} | {pred_c:<12}")

print("="*115)
print("Verification process completed using Original METAR Labels.")