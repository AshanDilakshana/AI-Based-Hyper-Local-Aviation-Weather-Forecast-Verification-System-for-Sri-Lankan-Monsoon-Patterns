from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
import datetime
import os

app = Flask(__name__)
CORS(app)

# Load trained models from the models directory
# Note: Ensure the paths are correct relative to the backend folder
# Load trained models from the models directory
try:
    # Use ../ to go out of backend folder and into models folder
    with open('../models/visibility_prediction_model.pkl', 'rb') as f:
        vis_model = pickle.load(f)

    with open('../models/cloud_prediction_model.pkl', 'rb') as f:
        cloud_model = pickle.load(f)
    print("Models loaded successfully!")
except Exception as e:
    print(f"Error loading models: {e}")

# In-memory storage for prediction history
prediction_history = []

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        temp = float(data['temp'])
        dew_point = float(data['dew_point'])
        rh = float(data['rh'])
        qnh = float(data['qnh'])

        # Calculate Dew Point Depression for feature engineering
        dp_depression = temp - dew_point
        
        # Create a dataframe for model input
        input_df = pd.DataFrame([[temp, dp_depression, rh, qnh]], 
                                columns=['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)'])

        # Generate predictions using loaded models
        vis_pred = int(vis_model.predict(input_df)[0])
        cloud_pred = int(cloud_model.predict(input_df)[0])

        # Define labels for cloud levels
        cloud_labels = {0: 'Clear', 1: 'Few', 2: 'Scattered', 3: 'Broken', 4: 'Overcast'}
        
        # Prepare the result object
        result = {
            'id': len(prediction_history) + 1,
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'visibility': 'LOW' if vis_pred == 1 else 'NORMAL',
            'cloud_level': cloud_labels.get(cloud_pred, 'Unknown'),
            'alert': True if vis_pred == 1 else False
        }

        # Save to history for verification tracking
        prediction_history.append(result)
        
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/history', methods=['GET'])
def get_history():
    # Return all previous predictions
    return jsonify(prediction_history)

if __name__ == '__main__':
    # Run server on port 8000
    app.run(port=8000, debug=True)