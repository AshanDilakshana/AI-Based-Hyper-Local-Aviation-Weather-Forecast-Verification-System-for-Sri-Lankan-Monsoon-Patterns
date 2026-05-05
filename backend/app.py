from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

CLOUD_LABELS = {
    0: "SKC (Sky Clear)",
    1: "FEW (Few Clouds)",
    2: "SCT (Scattered)",
    3: "BKN (Broken)",
    4: "OVC (Overcast)"
}

vis_model = None
cloud_model = None

def load_models():
    global vis_model, cloud_model
    base_path = os.path.dirname(os.path.abspath(__file__))
    vis_path = os.path.join(base_path, '..', 'models', 'visibility_prediction_model.pkl')
    cloud_path = os.path.join(base_path, '..', 'models', 'cloud_prediction_model.pkl')
    
    try:
        with open(vis_path, 'rb') as f:
            vis_model = pickle.load(f)
        with open(cloud_path, 'rb') as f:
            cloud_model = pickle.load(f)
        print("✅ Models loaded successfully.")
    except Exception as e:
        print(f"❌ Error loading models: {e}")

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        temp = float(data.get('temp', 0))
        dew = float(data.get('dew_point', 0))
        rh = float(data.get('rh', 0))
        qnh = float(data.get('qnh', 0))

        features = pd.DataFrame([[temp, temp-dew, rh, qnh]], 
                                columns=['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)'])

        v_pred = vis_model.predict(features)[0]
        c_pred = int(cloud_model.predict(features)[0])

        # Categorizing visibility for better understanding
        vis_category = "Poor"
        if v_pred >= 5000:
            vis_category = "Good"
        elif v_pred >= 2000:
            vis_category = "Moderate"

        return jsonify({
            "visibility_raw": float(v_pred),
            "visibility_category": vis_category,
            "cloud_level": CLOUD_LABELS.get(c_pred, "Unknown")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    load_models()
    app.run(port=8000, debug=True)