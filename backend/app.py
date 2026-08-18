import os
import pickle

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, '../Models/saved_models'))

try:
    with open(os.path.join(MODEL_PATH, 'xgb_cloud_model.pkl'), 'rb') as f:
        cloud_bundle = pickle.load(f)
    cloud_model = cloud_bundle['model']
    cloud_mapping = cloud_bundle['mapping']

    with open(os.path.join(MODEL_PATH, 'xgb_visibility_model.pkl'), 'rb') as f:
        vis_bundle = pickle.load(f)
    vis_model = vis_bundle['model']
    vis_mapping = vis_bundle['mapping']
    print("[SUCCESS] Mapped and loaded optimized 16-feature lookup models successfully!")
except Exception as e:
    print(f"[ERROR] Model Loading Error: {e}")

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        temp = float(data['temp'])
        dew = float(data['dew'])
        rh = float(data['rh'])
        qnh = float(data['qnh'])
        wind = float(data['wind'])
        
        # Mapped safely from dashboard payload names
        month = float(data.get('month', 6))
        hour = float(data.get('hour', 12))  # Matches dataset hour format (Time // 100)
        wind_dir = float(data.get('wind_dir', 180))
        weather_encoded = float(data.get('weather_encoded', 0))

        # Re-calculating interaction metrics
        dew_point_depression = temp - dew
        temp_rh = temp * rh
        wind_rh = wind * rh
        pressure_wind = qnh * wind
        rh_squared = rh ** 2

        feature_names = [
            'Month', 'Hour', 'Wind Dir.', 'Wind speed(Kts)', 'Dry tem(0C)', 'Dew point(0C)', 
            'RH(%)', 'QNH (hPa)', 'Dew_Point_Depression', 'Temp_RH', 'Wind_RH', 
            'Pressure_Wind', 'RH_Squared', 'Weather_Encoded'
        ]
        
        input_data = pd.DataFrame([[
            month, hour, wind_dir, wind, temp, dew, rh, qnh,
            dew_point_depression, temp_rh, wind_rh, pressure_wind, rh_squared, weather_encoded
        ]], columns=feature_names)

        # 🎯 FIXED: Force casting index to native Python int() to completely eliminate np.float32 mapping error
        cloud_raw_pred = cloud_model.predict(input_data)[0]
        cloud_idx = int(np.clip(np.round(cloud_raw_pred), 0, len(cloud_mapping) - 1))
        
        vis_raw_pred = vis_model.predict(input_data)[0]
        vis_idx = int(np.clip(np.round(vis_raw_pred), 0, len(vis_mapping) - 1))

        return jsonify({
            "visibility_prediction": int(vis_mapping[vis_idx]),
            "cloud_status": str(cloud_mapping[cloud_idx])
        })
    except Exception as e:
        print(f"⚠️ Prediction Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)