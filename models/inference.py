import pickle
import pandas as pd
import numpy as np

# 1. Load the trained models
# Using the professional names we set earlier
with open('models/visibility_prediction_model.pkl', 'rb') as f:
    vis_model = pickle.load(f)

with open('models/cloud_prediction_model.pkl', 'rb') as f:
    cloud_model = pickle.load(f)

# 2. Function to predict weather conditions based on manual input
def predict_weather(temp, dew_point, rh, qnh):
    # Calculate Dew Point Depression as we did in Feature Engineering
    dp_depression = temp - dew_point
    
    # Prepare the input data for the models
    input_data = pd.DataFrame([[temp, dp_depression, rh, qnh]], 
                              columns=['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)'])
    
    # Predict Visibility Status (1: Alert <5000m, 0: Normal)[cite: 1]
    vis_prediction = vis_model.predict(input_data)[0]
    
    # Predict Cloud Level (0-4)[cite: 1]
    cloud_prediction = cloud_model.predict(input_data)[0]
    
    # Map Cloud Level back to text labels for clarity[cite: 1]
    cloud_labels = {0: 'Clear (SKC/NSC)', 1: 'Few (FEW)', 2: 'Scattered (SCT)', 
                    3: 'Broken (BKN)', 4: 'Overcast (OVC)'}
    
    print("-" * 30)
    print("--- WEATHER PREDICTION RESULTS ---")
    print(f"Visibility Status: {'LOW (Alert <5000m)' if vis_prediction == 1 else 'NORMAL'}")
    print(f"Cloud Condition: {cloud_labels.get(cloud_prediction, 'Unknown')}")
    print("-" * 30)

# 3. Test with some sample data (Example values)
# You can change these values to test different scenarios
print("Testing Model with sample values...")
predict_weather(temp=28.5, dew_point=25.0, rh=82.0, qnh=1012.5)