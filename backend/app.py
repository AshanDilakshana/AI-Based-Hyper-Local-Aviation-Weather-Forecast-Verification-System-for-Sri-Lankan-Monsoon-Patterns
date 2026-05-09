from flask import Flask, request, jsonify
import pickle
import pandas as pd
import numpy as np
import os

app = Flask(__name__)

# 1. Setup paths to find the trained models
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Looking into models/models/ folder for the .pkl files
MODEL_PATH = os.path.join(BASE_DIR, '../models/models')

# 2. Load the trained Random Forest models
# We use global variables so they are accessible in the predict route
try:
    with open(os.path.join(MODEL_PATH, 'random_forest_visibility.pkl'), 'rb') as f:
        vis_model = pickle.load(f)
    with open(os.path.join(MODEL_PATH, 'random_forest_cloud.pkl'), 'rb') as f:
        cloud_model = pickle.load(f)
    print("✅ Successfully loaded Weather-Only models (Month/Time removed)!")
except Exception as e:
    print(f"❌ Model Loading Error: {e}")

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get data from the frontend request
        data = request.json
        
        # Extract basic weather parameters only
        temp = float(data['temp'])
        dew = float(data['dew'])
        rh = float(data['rh'])
        qnh = float(data['qnh'])
        
        # Calculate Dew Point Depression (Feature Engineering used during training)
        dew_point_depression = temp - dew
        
        # 3. Create a DataFrame for prediction
        # The column names MUST match the features used in 'random_forest_model.py'
        feature_names = ['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']
        input_data = pd.DataFrame([[temp, dew_point_depression, rh, qnh]], 
                                 columns=feature_names)
        
        # 4. Perform AI predictions
        vis_prediction = vis_model.predict(input_data)[0]
        cloud_pred_idx = cloud_model.predict(input_data)[0]
        
        # 5. Map numerical cloud index back to aviation labels
        cloud_mapping = {0: 'OVC', 1: 'BKN', 2: 'SCT', 3: 'FEW', 4: 'NSC'}
        cloud_status = cloud_mapping.get(cloud_pred_idx, "NSC")

        # Return the results to the Dashboard
        return jsonify({
            "visibility_prediction": float(vis_prediction),
            "cloud_status": cloud_status
        })
        
    except Exception as e:
        # Print the exact error in the terminal for debugging
        print(f"⚠️ Prediction API Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Running the Flask server on port 5000
    app.run(debug=True, port=5000)