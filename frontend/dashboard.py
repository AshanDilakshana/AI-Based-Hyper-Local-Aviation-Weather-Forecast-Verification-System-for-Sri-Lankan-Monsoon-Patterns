import os
import re
import sqlite3
import requests
import streamlit as st

st.set_page_config(page_title="BIA Control - Industrial Takeoff Verification", layout="wide")
st.title("🛫 BIA Control - Industrial Takeoff Verification")
st.markdown("---")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '../weather_data.db'))

# Direction mapping for aviation METAR remarks
DIR_MAP = {
    'N': 'North', 'S': 'South', 'E': 'East', 'W': 'West',
    'NE': 'North-East', 'NW': 'North-West', 'SE': 'South-East', 'SW': 'South-West',
    'E/S': 'East to South', 'N/E': 'North to East', 'S/W': 'South to West', 'N/W': 'North to West'
}

def explain_cloud(cloud_code):
    raw_code = str(cloud_code).strip().upper()
    
    if raw_code in ['SKC', 'NSC', 'CLR', 'NONE', 'NIL']:
        return "Clear sky. No clouds (0/8 sky covered)."

    layers = []
    has_cb = 'CB' in raw_code
    has_tcu = 'TCU' in raw_code

    # Extract standard cloud layers (handles both 2-digit and 3-digit altitude codes)
    matches = re.findall(r'(FEW|SCT|BKN|OVC)(\d{2,3})?', raw_code)
    
    # Intuitive fractional sky coverage representations
    coverage_names = {
        'FEW': 'Few clouds (1/8–2/8 sky covered)',
        'SCT': 'Scattered clouds (3/8–4/8 sky covered)',
        'BKN': 'Broken cloud cover (5/8–7/8 sky covered)',
        'OVC': 'Overcast sky (8/8 fully covered)'
    }

    for cov, alt in matches:
        cov_text = coverage_names.get(cov, cov)
        if alt:
            altitude_ft = int(alt) * 100
            layers.append(f"{cov_text} at {altitude_ft:,} ft")
        else:
            layers.append(cov_text)

    direction_notes = []
    for token in raw_code.split():
        if token in DIR_MAP:
            direction_notes.append(DIR_MAP[token])

    explanation_parts = []
    if layers:
        explanation_parts.append("Observed: " + ", ".join(layers) + ".")
    else:
        explanation_parts.append(f"Cloud pattern: {raw_code}.")

    if has_cb:
        cb_text = "Thunderstorm clouds (CB) detected"
        if direction_notes:
            cb_text += f" towards {' / '.join(direction_notes)}"
        cb_text += ", indicating active thunderstorm and rain conditions."
        explanation_parts.append(cb_text)
    elif has_tcu:
        explanation_parts.append("Developing storm clouds (TCU) detected.")
    elif direction_notes:
        explanation_parts.append(f"Cloud movement/location noted towards {' / '.join(direction_notes)}.")

    return " ".join(explanation_parts)

def explain_visibility(visibility):
    vis_int = int(float(visibility))
    return f"Predicted visibility is {vis_int} meters."


st.sidebar.header("📡 Live Aviation Data Feed")
st.sidebar.info("Live data will be automatically fetched from the database when a forecast is generated.")

st.markdown("### Industrial Prediction Engine")
st.write("This automated system uses the latest synchronized METAR readings from the database to generate hyper-local Cloud and Visibility forecasts for BIA take-off operations.")

if st.button("Generate Live Takeoff Forecast", type="primary"):
    # Dummy payload since the FastAPI backend automatically fetches the recent row from DB
    payload = {
        "temp": 0, "dew": 0, "rh": 0, "qnh": 0, "wind": 0,
        "month": 1, "hour": 12, "wind_dir": 0, "weather_encoded": 0
    }
    
    try:
        # Updated to FastAPI port 8000
        response = requests.post("http://127.0.0.1:8000/predict", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            vis_val = result.get('visibility_prediction', 0)
            cloud_status = result.get('cloud_status', 'UNKNOWN')

            st.success("Forecast generated successfully based on live data!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.info("#### 🌫️ Visibility Details")
                st.write(f"Predicted Visibility: **{vis_val} m**")
                st.write(f"*Analysis:* {explain_visibility(vis_val)}")
            
            with col2:
                st.warning("#### ☁️ Cloud Details")
                st.write(f"Predicted Cloud Condition: **{cloud_status}**")
                st.write(f"*Analysis:* {explain_cloud(cloud_status)}")
        else:
            st.error(f"Backend Error: {response.text}")

    except Exception as e:
        st.error(f"Error: Backend is not running on port 8000. Please start main.py. Details: {e}")