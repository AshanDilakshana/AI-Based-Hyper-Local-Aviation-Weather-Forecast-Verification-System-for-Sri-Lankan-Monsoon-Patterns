import streamlit as st
import requests
import pickle
import os

st.set_page_config(page_title="BIA Takeoff Safety Dashboard", layout="wide")
st.title("🛫 BIA Control - Takeoff Weather Verification")
st.markdown("---")

# Load weather encoder safely to show text weather names in sidebar dropdown
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENCODER_PATH = os.path.join(BASE_DIR, '../models/saved_models/weather_encoder.pkl')

weather_options = ['NONE', 'RA', 'TS', 'SHRA', 'BR', 'DZ', 'HZ']
try:
    with open(ENCODER_PATH, 'rb') as f:
        le_weather = pickle.load(f)
    weather_options = list(le_weather.classes_)
except:
    pass

st.sidebar.header("Current Weather Observations")

# 1. Base Meteorological Inputs
dry_temp = st.sidebar.number_input("Dry Temperature (°C)", value=31.0, format="%.2f")
dew_temp = st.sidebar.number_input("Dew Point (°C)", value=24.0, format="%.2f")
rh_pct = st.sidebar.number_input("Relative Humidity (%)", value=66.0)
pressure = st.sidebar.number_input("Pressure (QNH hPa)", value=1007.40, format="%.2f")
wind_speed = st.sidebar.number_input("Wind Speed (Kts)", value=12.0, format="%.2f")

# 2. Advanced Feature Inputs (No Dropdown for Time - Direct Type Input)
month = st.sidebar.slider("Month of the Year", min_value=1, max_value=12, value=6)

#  Direct Type Input matching exact dataset HHMM format (e.g., 1344, 0052)
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

# Explanation Functions Shared by User
def explain_cloud(cloud_code):
    cloud_code = str(cloud_code).upper()
    if 'CB' in cloud_code:
        return "Cumulonimbus cloud was reported, which may indicate thunderstorm activity."
    elif cloud_code.startswith('SKC') or cloud_code.startswith('NSC'):
        return "No significant cloud was reported."
    elif cloud_code.startswith('FEW'):
        return "Few clouds were reported."
    elif cloud_code.startswith('SCT'):
        return "Scattered clouds were reported."
    elif cloud_code.startswith('BKN'):
        return "Broken cloud cover was reported."
    elif cloud_code.startswith('OVC'):
        return "Overcast sky conditions were reported."
    else:
        return "Cloud condition predicted from METAR weather data."

def explain_visibility(visibility):
    if int(visibility) == 9999:
        return "Visibility is 10 kilometers or more."
    return f"Predicted horizontal visibility is {int(float(visibility))} metres."

if st.sidebar.button("Generate Takeoff Forecast"):
    weather_encoded = weather_options.index(selected_weather) if selected_weather in weather_options else 0
    
    # ⚙️ Convert the typed HHMM format (e.g., 1344) into the training feature format (13)
    calculated_hour = int(metar_time // 100)
    
    payload = {
        "temp": dry_temp, 
        "dew": dew_temp, 
        "rh": rh_pct, 
        "qnh": pressure, 
        "wind": wind_speed,
        "month": month, 
        "hour": calculated_hour,  # Passed cleanly as the processed structural integer
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
            
            st.markdown("####  Visibility Details")
            st.write(f"Predicted Visibility: **{vis_val} m**")
            st.write(f"*Meaning:* {explain_visibility(vis_val)}")

            st.markdown("---")

            st.markdown("####  Cloud Details")
            st.write(f"Predicted Cloud Condition: **{cloud_status}**")
            st.write(f"*Meaning:* {explain_cloud(cloud_status)}")

    except Exception as e:
        st.error("Error: Backend is not running. Please start app.py first.")