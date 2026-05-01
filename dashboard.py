import streamlit as st
import requests
import datetime

# 1. Page Configuration
st.set_page_config(page_title="Pilot Portal - Aviation Weather", layout="centered")

st.title("🛩️ Pilot Weather Portal")
st.markdown("### AI-Based Aviation Weather Forecast Verification")
st.write("Sri Lankan Monsoon Patterns Analysis")

# 2. Input Form for Pilots
with st.form("weather_input"):
    st.write("#### Enter Current Weather Parameters")
    
    col1, col2 = st.columns(2)
    with col1:
        temp = st.number_input("Dry Temp (°C)", value=28.0, step=0.1)
        dew_point = st.number_input("Dew Point (°C)", value=25.0, step=0.1)
    
    with col2:
        rh = st.number_input("Relative Humidity (%)", value=85.0, step=1.0)
        qnh = st.number_input("QNH (hPa)", value=1010.0, step=0.1)
    
    submit = st.form_submit_button("Get AI Prediction")

# 3. Connection to Backend API (Flask)
if submit:
    # Data to send to your app.py backend
    payload = {
        "temp": temp,
        "dew_point": dew_point,
        "rh": rh,
        "qnh": qnh
    }
    
    try:
        # Calling your running backend on port 8000
        response = requests.post("http://127.0.0.1:8000/api/predict", json=payload)
        result = response.json()
        
        st.divider()
        st.subheader("Prediction Results")
        
        # 4. Display Results with visual alerts
        if result['alert']:
            st.error(f"🚨 VISIBILITY STATUS: {result['visibility']} (Alert <5000m)")
        else:
            st.success(f"✅ VISIBILITY STATUS: {result['visibility']} (Normal)")
            
        st.info(f"☁️ CLOUD LEVEL: {result['cloud_level']}")
        st.caption(f"Generated at: {result['timestamp']}")
        
    except Exception as e:
        st.error(f"Could not connect to Backend: {e}")