import pandas as pd
import pickle
import numpy as np
from sklearn.metrics import confusion_matrix, accuracy_score

# 1. Load the trained models
with open('models/visibility_prediction_model.pkl', 'rb') as f:
    vis_model = pickle.load(f)

with open('models/cloud_prediction_model.pkl', 'rb') as f:
    cloud_model = pickle.load(f)

# 2. Load the dataset for verification
# We use the aviation_weather_features.csv which has the calculated features
df = pd.read_csv('data/aviation_weather_features.csv')

# Use a sample of 10-20 rows for verification
test_sample = df.head(20).copy()

# 3. Define the input features for the AI model
feature_cols = ['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']

# 4. Generate Predictions from the AI models
test_sample['Predicted_Visibility'] = vis_model.predict(test_sample[feature_cols])
test_sample['Predicted_Cloud'] = cloud_model.predict(test_sample[feature_cols])

# 5. Compare Predictions with Actual Data (Verification)
print("\n" + "="*60)
print("       FORECAST VERIFICATION RESULTS (Sample 20 Rows)")
print("="*60)

for index, row in test_sample.iterrows():
    print(f"Row {index+1}:")
    # Visibility Verification
    v_actual = "LOW" if row['Visibility_Status'] == 1 else "NORMAL"
    v_pred = "LOW" if row['Predicted_Visibility'] == 1 else "NORMAL"
    v_status = "✅ MATCH" if v_actual == v_pred else "❌ MISMATCH"
    
    # Cloud Verification
    c_actual = int(row['Cloud_Level'])
    c_pred = int(row['Predicted_Cloud'])
    c_status = "✅ MATCH" if c_actual == c_pred else "❌ MISMATCH"
    
    print(f"  Visibility: Actual={v_actual} | Predicted={v_pred} -> {v_status}")
    print(f"  Cloud Level: Actual={c_actual} | Predicted={c_pred} -> {c_status}")
    print("-" * 60)

# 6. Overall Accuracy for this sample
vis_acc = accuracy_score(test_sample['Visibility_Status'], test_sample['Predicted_Visibility'])
print(f"\nOverall Visibility Verification Accuracy: {vis_acc * 100:.2f}%")
print("="*60)