import os
import pickle
import re
import requests
import streamlit as st

st.set_page_config(page_title="BIA Takeoff Safety Dashboard", layout="wide")
st.title("🛫 BIA Control - Takeoff Weather Verification")
st.markdown("---")

# Load weather encoder safely to show text weather names in sidebar dropdown
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENCODER_PATH = os.path.abspath(os.path.join(BASE_DIR, '../models/saved_models/weather_encoder.pkl'))

weather_options = ['NONE', 'RA', 'TS', 'SHRA', 'BR', 'DZ', 'HZ']
try:
    with open(ENCODER_PATH, 'rb') as f:
        le_weather = pickle.load(f)
    weather_options = list(le_weather.classes_)
except Exception:
    pass

st.sidebar.header("Current Weather Observations")

# 1. Base Meteorological Inputs
dry_temp = st.sidebar.number_input("Dry Temperature (°C)", value=31.0, format="%.2f")
dew_temp = st.sidebar.number_input("Dew Point (°C)", value=24.0, format="%.2f")
rh_pct = st.sidebar.number_input("Relative Humidity (%)", value=66.0)
pressure = st.sidebar.number_input("Pressure (QNH hPa)", value=1007.40, format="%.2f")
wind_speed = st.sidebar.number_input("Wind Speed (Kts)", value=12.0, format="%.2f")

# 2. Advanced Feature Inputs
month = st.sidebar.slider("Month of the Year", min_value=1, max_value=12, value=6)

metar_time = st.sidebar.number_input(
    "Time (UTC format - e.g., 1344, 0052, 2310)", 
    min_value=0, 
    max_value=2359, 
    value=1200, 
    step=1,
    help="Enter the exact 4-digit UTC time from the METAR record."
)

wind_dir = st.sidebar.number_input("Wind Direction (Degrees)", value=180.0, format="%.2f")
selected_weather = st.sidebar.selectbox("Current METAR Weather Condition", options=weather_options)

st.sidebar.markdown("---")

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
    return f"predicted visibility is {vis_int} meters."

if st.sidebar.button("Generate Takeoff Forecast"):
    weather_encoded = weather_options.index(selected_weather) if selected_weather in weather_options else 0
    calculated_hour = int(metar_time // 100)
    
    payload = {
        "temp": dry_temp, 
        "dew": dew_temp, 
        "rh": rh_pct, 
        "qnh": pressure, 
        "wind": wind_speed,
        "month": month, 
        "hour": calculated_hour,
        "wind_dir": wind_dir, 
        "weather_encoded": weather_encoded
    }
    
    try:
        response = requests.post("http://127.0.0.1:5000/predict", json=payload)
        result = response.json()
        
        if "error" in result:
            st.error(f"Backend Error: {result['error']}")
        else:
            vis_val = result['visibility_prediction']
            cloud_status = result['cloud_status']

            st.subheader("Verification Result")
            st.markdown("---")
            
            st.markdown("#### Visibility Details")
            st.write(f"Predicted Visibility: **{vis_val} m**")
            st.write(f"*Meaning:* {explain_visibility(vis_val)}")

            st.markdown("---")

            st.markdown("####  Cloud Details")
            st.write(f"Predicted Cloud Condition: **{cloud_status}**")
            st.write(f"*Meaning:* {explain_cloud(cloud_status)}")

    except Exception:
        st.error("Error: Backend is not running. Please start app.py first.")