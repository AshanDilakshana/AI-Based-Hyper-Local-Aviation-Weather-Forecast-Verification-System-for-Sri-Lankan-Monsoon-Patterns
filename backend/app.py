from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

# Aviation-standard cloud descriptions for better user understanding
# Maps technical codes to human-readable safety status
CLOUD_DESCRIPTIONS = {
    0: "SKC - Clear Sky (Safe for takeoff)",
    1: "FEW - Few Clouds (Minimal impact on visibility)",
    2: "SCT - Scattered Clouds (Moderate coverage)",
    3: "BKN - Broken Clouds (High coverage - Caution required)",
    4: "OVC - Overcast (Full coverage - High risk of low ceiling)"
}

vis_model = None
cloud_model = None

def load_models():
    """
    Loads the best performing XGBoost models from the models directory.
    Uses absolute pathing to ensure stability across different environments.
    """
    global vis_model, cloud_model
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Path configuration for the trained XGBoost pkl files
    vis_path = os.path.join(base_path, '..', 'models', 'models', 'xgboost_visibility.pkl')
    cloud_path = os.path.join(base_path, '..', 'models', 'models', 'xgboost_cloud.pkl')
    
    try:
        with open(vis_path, 'rb') as f:
            vis_model = pickle.load(f)
        with open(cloud_path, 'rb') as f:
            cloud_model = pickle.load(f)
        print("✅ Success: XGBoost Aviation Models loaded.")
    except Exception as e:
        print(f"❌ Error: Could not load models. Check paths. {e}")

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    API Endpoint to receive weather data and return flight safety predictions.
    Calculates Dew Point Depression internally as an engineered feature.
    """
    try:
        data = request.get_json()
        temp = float(data.get('temp', 0))
        dew = float(data.get('dew_point', 0))
        rh = float(data.get('rh', 0))
        qnh = float(data.get('qnh', 0))

        # Preparing the input features for the model
        # Dew Point Depression is calculated here (Temp - Dew Point)
        features = pd.DataFrame([[temp, temp-dew, rh, qnh]], 
                                columns=['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)'])

        # Generate raw predictions from XGBoost models
        v_pred = vis_model.predict(features)[0]
        c_pred = int(cloud_model.predict(features)[0])

        # --- Aviation Safety Logic for Panel Presentation ---
        # Categorizing visibility according to ICAO (International Civil Aviation Organization) rules
        if v_pred >= 5000:
            vis_info = "VFR Conditions (Visual Flight Rules) - Safe for takeoff"
            safety_status = "Good"
        elif v_pred >= 1500:
            vis_info = "MVFR (Marginal VFR) - Caution: Moderate Visibility"
            safety_status = "Moderate"
        else:
            vis_info = "IFR Conditions (Instrument Flight Rules) - Dangerous: Low Visibility"
            safety_status = "Poor"

        return jsonify({
            "visibility_raw": f"{int(v_pred)}m",
            "visibility_status": vis_info,
            "visibility_category": safety_status,
            "cloud_level": CLOUD_DESCRIPTIONS.get(c_pred, "Unknown Cloud Conditions")
        })
        
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    load_models()
    # Starting the backend server on port 8000
    app.run(port=8000, debug=True)