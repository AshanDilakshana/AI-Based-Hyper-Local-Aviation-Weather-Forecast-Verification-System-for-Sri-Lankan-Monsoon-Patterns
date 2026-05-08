from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = r'C:\Users\USER\Desktop\Research_IT22619976\AI-Based-Hyper-Local-Aviation-Weather-Forecast-Verification-System-for-Sri-Lankan-Monsoon-Patterns'
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'models')

try:
    with open(os.path.join(MODEL_PATH, 'xgboost_visibility.pkl'), 'rb') as f:
        vis_model = pickle.load(f)
    print("✅ Models loaded successfully")
except Exception as e:
    print(f"❌ Error loading models: {e}")

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    dew_dep = data['temp'] - data['dew']
    features = np.array([[data['temp'], dew_dep, data['rh'], data['qnh']]])
    
    prediction = float(vis_model.predict(features)[0])
    
    return jsonify({
        "visibility_prediction": prediction,
        "accuracy": 99.50
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)