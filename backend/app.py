from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
import datetime
import os

app = Flask(__name__)
CORS(app)

# Global variables for models
vis_model = None
cloud_model = None

# Professional mapping for cloud levels with coverage details
CLOUD_LABELS = {
    0: "Clear (Sky Clear - No Clouds)",
    1: "Few (FEW: 1/8 - 2/8 sky covered)",
    2: "Scattered (SCT: 3/8 - 4/8 sky covered)",
    3: "Broken (BKN: 5/8 - 7/8 sky covered)",
    4: "Overcast (OVC: 8/8 sky covered)"
}

def load_models():
    """Load the trained machine learning models."""
    global vis_model, cloud_model
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        vis_path = os.path.join(base_path, '../models/visibility_prediction_model.pkl')
        cloud_path = os.path.join(base_path, '../models/cloud_prediction_model.pkl')

        with open(vis_path, 'rb') as f:
            vis_model = pickle.load(f)
        with open(cloud_path, 'rb') as f:
            cloud_model = pickle.load(f)
        print("Models loaded successfully!")
    except Exception as e:
        print(f"Error loading models: {e}")

@app.route('/api/predict', methods=['POST'])
def predict():
    """Handle prediction requests from the Streamlit dashboard."""
    try:
        data = request.json
        temp = float(data['temp'])
        dew_point = float(data['dew_point'])
        rh = float(data['rh'])
        qnh = float(data['qnh'])
        
        # Feature Engineering: Calculate Dew Point Depression
        dp_depression = temp - dew_point
        input_df = pd.DataFrame([[temp, dp_depression, rh, qnh]], 
                                columns=['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)'])

        vis_pred = vis_model.predict(input_df)[0]
        cloud_pred = cloud_model.predict(input_df)[0]

        # Specific wording as per user request: "Visibility - SAFE: Operations Permitted"
        if vis_pred == 1:
            vis_status = "Visibility - CAUTION: Restricted"
            is_alert = True
        else:
            vis_status = "Visibility - SAFE: Operations Permitted"
            is_alert = False

        return jsonify({
            "visibility": vis_status,
            "cloud_level": CLOUD_LABELS.get(cloud_pred, "Unknown Data"),
            "alert": is_alert,
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S UTC")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    load_models()
    app.run(port=8000, debug=False)