import streamlit as st
import requests

st.set_page_config(page_title="Aviation Weather Center", layout="wide")

# Custom UI Styling to match your layout
st.markdown("""
    <style>
    .main { background-color: #0b0e14; color: #ffffff; }
    .metric-card { 
        background-color: #161a23; padding: 60px; border-radius: 15px; 
        border: 1px solid #2d323e; text-align: center; margin-top: 20px;
    }
    .vis-label { color: #8e94a5; text-transform: uppercase; letter-spacing: 2px; font-size: 1rem; }
    .vis-val { font-size: 5rem; font-weight: bold; color: #ffffff; margin: 10px 0; }
    .cloud-val { color: #2e66ff; font-size: 2rem; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

col_in, col_out = st.columns([1, 2])

with col_in:
    st.title("✈️ BIA Control")
    st.write("Meteorological Data Inputs")
    
    # Input Fields
    temp = st.number_input("Dry Temperature (°C)", value=30.5, step=0.1)
    dew = st.number_input("Dew Point (°C)", value=25.0, step=0.1)
    rh = st.number_input("Relative Humidity (%)", value=75, step=1)
    qnh = st.number_input("Barometric Pressure (QNH) (hPa)", value=1010.1, step=0.1)
    
    generate = st.button("Generate Forecast", use_container_width=True)

with col_out:
    if generate:
        try:
            # Backend API Request
            payload = {"temp": temp, "dew_point": dew, "rh": rh, "qnh": qnh}
            res = requests.post("http://127.0.0.1:8000/api/predict", json=payload).json()

            v_raw = res.get('visibility_raw', 0)
            v_cat = res.get('visibility_category', 'Unknown')
            c_lvl = res.get('cloud_level', 'Unknown')

            # Displaying the focused output
            st.markdown(f"""
            <div class="metric-card">
                <p class="vis-label">Predicted Visibility</p>
                <div class="vis-val">{int(v_raw)}m <span style="font-size: 1.5rem; color: #8e94a5;">({v_cat})</span></div>
                <div style="margin: 30px auto; width: 50%; border-top: 1px solid #2d323e;"></div>
                <p class="vis-label">Cloud Coverage</p>
                <p class="cloud-val">{c_lvl}</p>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error("Connection Error: Ensure backend (app.py) is running.")
    else:
        st.info("Enter meteorological data on the left to generate runway safety forecasts.")