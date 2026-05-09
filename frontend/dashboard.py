import streamlit as st
import requests

# Professional page setup
st.set_page_config(page_title="BIA Takeoff Safety Dashboard", layout="wide")

st.title("🛫 BIA Control - Takeoff Weather Verification")
st.markdown("---")

# 1. Sidebar Inputs - Meteorological Data Only
st.sidebar.header("Current Weather Observations")

dry_temp = st.sidebar.number_input("Dry Temperature (°C)", value=31.0, format="%.2f")
dew_temp = st.sidebar.number_input("Dew Point (°C)", value=24.0, format="%.2f")
rh_pct = st.sidebar.number_input("Relative Humidity (%)", value=66.0)
pressure = st.sidebar.number_input("Pressure (QNH hPa)", value=1007.40, format="%.2f")

st.sidebar.markdown("---")

if st.sidebar.button("Generate Takeoff Forecast"):
    # Data payload for prediction
    payload = {
        "temp": dry_temp,
        "dew": dew_temp,
        "rh": rh_pct,
        "qnh": pressure
    }
    
    try:
        # Requesting results from Flask backend
        response = requests.post("http://127.0.0.1:5000/predict", json=payload)
        result = response.json()
        
        if "error" in result:
            st.error(f"Backend Error: {result['error']}")
        else:
            vis_val = result['visibility_prediction']
            cloud_status = result['cloud_status']

            st.subheader("Verification Result")
            
            # Dictionary for detailed Cloud Meanings (as you liked before)
            cloud_info = {
                'NSC': {'desc': 'NSC (No Significant Clouds)', 'meaning': 'Clear sky. Safe for takeoff.'},
                'FEW': {'desc': 'FEW (Few Clouds)', 'meaning': '1/8 to 2/8 coverage. Minimal impact on flight.'},
                'SCT': {'desc': 'SCT (Scattered Clouds)', 'meaning': '3/8 to 4/8 coverage. Safe for Visual flight.'},
                'BKN': {'desc': 'BKN (Broken Clouds)', 'meaning': '5/8 to 7/8 coverage. Significant cloud ceiling detected.'},
                'OVC': {'desc': 'OVC (Overcast)', 'meaning': 'Full sky coverage. Visibility highly restricted.'}
            }
            
            info = cloud_info.get(cloud_status, {'desc': cloud_status, 'meaning': 'N/A'})

            # 2. VFR/IFR Logic Display
            if vis_val >= 5000 and cloud_status not in ['BKN', 'OVC']:
                st.success("### ✅ Status: SAFE (VFR)")
                st.info("**VFR (Visual Flight Rules):** Conditions are clear. Pilot can take off using visual references.")
            else:
                st.error("### ❌ Status: RESTRICTED (IFR)")
                st.warning("**IFR (Instrument Flight Rules):** Low visibility or thick clouds. Pilot must rely on instruments.")

            # 3. Detailed Cloud Information Display (Back by popular demand)
            st.markdown("#### Cloud Details")
            st.write(f"**Condition:** {info['desc']}")
            st.write(f"**Aviation Meaning:** {info['meaning']}")
            
            # Note: Numerical visibility value remains hidden as requested.

    except Exception as e:
        st.error("Error: Backend is not running. Please start app.py first.")