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

        st.subheader("Aviation Weather Verification Result")
        
        # Displaying Visibility and Status clearly for the panel
        if vis_val >= 5000:
            st.success("### ✅ Prediction: HIGH VISIBILITY")
            st.info(f"**Aviation Status:** VFR - Visual Flight Rules (Safe for Normal Takeoff)")
            st.markdown(f"""
            * **Visibility Level:** Clear (Above 5,000m)
            * **Cloud Condition:** NSC (No Significant Clouds) - No operational risk.
            * **Pilot Guidance:** Visual navigation is sufficient.
            """)
        else:
            st.error("### ⚠️ Prediction: LOW VISIBILITY")
            st.warning(f"**Aviation Status:** IFR - Instrument Flight Rules (Caution Required)")
            st.markdown(f"""
            * **Visibility Level:** Restricted (Below 5,000m)
            * **Cloud Condition:** BKN/OVC (Broken or Overcast) - Low visibility risk.
            * **Pilot Guidance:** Must use cockpit instruments for navigation.
            """)

        st.markdown("---")
        st.write(f"**Model Accuracy (XGBoost):** {result['accuracy']}%")

    except Exception as e:
        st.error("Error connecting to Backend. Ensure app.py is running on Port 5000.")

else:
    st.info("Enter meteorological data and click 'Generate Takeoff Forecast' to verify safety.")