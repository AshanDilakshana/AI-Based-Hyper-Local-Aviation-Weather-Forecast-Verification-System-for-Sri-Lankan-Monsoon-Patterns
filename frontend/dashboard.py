import streamlit as st
import requests

st.set_page_config(page_title="BIA Takeoff Safety Dashboard", layout="wide")

st.title("🛫 BIA Control - Takeoff Weather Verification")
st.markdown("---")

st.sidebar.header("Current Weather Observations")
dry_temp = st.sidebar.number_input("Dry Temperature (°C)", value=31.0)
dew_temp = st.sidebar.number_input("Dew Point (°C)", value=24.0)
rh_pct = st.sidebar.number_input("Relative Humidity (%)", value=66.0)
pressure = st.sidebar.number_input("Pressure (QNH hPa)", value=1007.4)

if st.sidebar.button("Generate Takeoff Forecast"):
    data = {
        "temp": dry_temp,
        "dew": dew_temp,
        "rh": rh_pct,
        "qnh": pressure
    }
    
    try:
        response = requests.post("http://127.0.0.1:5000/predict", json=data)
        result = response.json()
        vis_val = result['visibility_prediction']

        st.subheader("Predicted Aviation Safety Status")
        
        if vis_val >= 5000:
            st.success("### STATUS: VFR - Visual Flight Rules")
            st.info("**CONDITION:** SKC (Sky Clear) - No clouds detected. Visibility is optimal for manual takeoff.")
            st.write("✅ Safe for standard takeoff procedures.")
        else:
            st.error("### STATUS: IFR - Instrument Flight Rules")
            st.warning("**CONDITION:** BKN/OVC (Broken/Overcast) - Low ceiling and cloud cover detected. Use automated systems.")
            st.write("⚠️ Caution: Restricted visibility conditions.")

        st.markdown("---")
        st.write(f"**Model Accuracy (XGBoost):** {result['accuracy']}%")

    except Exception as e:
        st.error("Error connecting to Backend. Ensure app.py is running on Port 5000.")

else:
    st.info("Enter weather data and click 'Generate Takeoff Forecast'.")