from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd

app = Flask(__name__)
CORS(app) # Allows cross-origin requests from your frontend

# Load the trained model (Ensure the path points to your best model)
MODEL_PATH = '../models/Random_Forest/random_forest_model.pkl'
try:
    model = joblib.load(MODEL_PATH)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        # Get JSON data from the frontend
        data = request.json
        
        # Convert incoming data to a DataFrame (must match the features used in training)
        input_data = pd.DataFrame([data])
        
        # Make prediction
        prediction = model.predict(input_data)[0]
        
        # Determine stability warning based on predicted pressure drop
        # (Example threshold: a drop greater than 2 hPa might trigger an alert)
        status = "Warning: High Instability Expected" if prediction < -2.0 else "Stable"
        
        return jsonify({
            'predicted_qnh_change': round(prediction, 3),
            'stability_status': status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)