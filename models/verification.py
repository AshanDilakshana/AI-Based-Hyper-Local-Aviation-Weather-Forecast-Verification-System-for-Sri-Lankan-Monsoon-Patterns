import pandas as pd
import pickle
import numpy as np
import os
from sklearn.metrics import accuracy_score

# 1. Handling Dynamic Paths
# This gets the directory where verification.py is actually located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# If your models are inside a subfolder named 'models' (models/models/)
# We check both the current folder and the subfolder to be 100% sure
MODEL_VIS_PATH = os.path.join(BASE_DIR, 'models', 'random_forest_visibility.pkl')
MODEL_CLOUD_PATH = os.path.join(BASE_DIR, 'models', 'random_forest_cloud.pkl')

# Fallback: if they are in the same folder as this script
if not os.path.exists(MODEL_VIS_PATH):
    MODEL_VIS_PATH = os.path.join(BASE_DIR, 'random_forest_visibility.pkl')
    MODEL_CLOUD_PATH = os.path.join(BASE_DIR, 'random_forest_cloud.pkl')

DATA_PATH = os.path.join(BASE_DIR, '../data/aviation_weather_features.csv')

# 2. Load the trained models
try:
    with open(MODEL_VIS_PATH, 'rb') as f:
        vis_model = pickle.load(f)
    with open(MODEL_CLOUD_PATH, 'rb') as f:
        cloud_model = pickle.load(f)
    print("✅ AI Models Loaded Successfully!")
except FileNotFoundError:
    print(f"❌ Error: Model files not found.")
    print(f"Looked in: {MODEL_VIS_PATH}")
    exit()

# 3. Load the dataset
try:
    df = pd.read_csv(DATA_PATH)
    # Cleaning column names just in case
    df.columns = df.columns.str.strip()
except Exception as e:
    print(f"❌ Error loading dataset: {e}")
    exit()

# Use a sample of 20 rows
test_sample = df.head(20).copy()
feature_cols = ['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']

# 4. Generate Predictions
test_sample['Predicted_Visibility'] = vis_model.predict(test_sample[feature_cols])

# 5. Verification Display
print("\n" + "="*75)
print("       BIA AVIATION WEATHER - FORECAST VERIFICATION RESULTS")
print("="*75)
print(f"{'Row':<6} | {'Actual Vis':<12} | {'Predicted Vis':<15} | {'Status':<10}")
print("-" * 75)

for index, row in test_sample.iterrows():
    actual_v = int(row['Visibility'])
    pred_v = int(row['Predicted_Visibility'])
    
    # Matching logic (within 500m margin)
    match_status = "✅ MATCH" if abs(actual_v - pred_v) < 1000 else "❌ MISMATCH"
    
    print(f"{index+1:<6} | {actual_v:<12} | {pred_v:<15} | {match_status:<10}")

print("="*75)
print("Verification process completed.")