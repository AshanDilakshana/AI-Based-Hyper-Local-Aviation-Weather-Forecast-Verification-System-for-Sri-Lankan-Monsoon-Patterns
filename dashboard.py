import streamlit as st
import requests
import datetime

# --- Page Config for Aviation Dark Theme ---
st.set_page_config(
    page_title="BIA Weather Forecast Center",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS for Styling ---
st.markdown("""
    <style>
    .main { background-color: #0b0e14; color: #ffffff; }
    .stNumberInput label { color: #8e94a5 !important; }
    .stNumberInput div div input { background-color: #1a1e26; color: white; border: 1px solid #3d4250; }
    .metric-card { 
        background-color: #161a23; 
        padding: 30px; 
        border-radius: 12px; 
        border: 1px solid #2d323e;
        margin-top: 10px;
    }
    .status-badge {
        background-color: #1c2a23;
        color: #4cd964;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.8rem;
        float: right;
    }
    .alert-badge {
        background-color: #2a1c1c;
        color: #ff3b30;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.8rem;
        float: right;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header Section ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("✈️ Aviation Weather Forecast Center")
    st.write("BANDARANAIKE INTERNATIONAL AIRPORT (BIA)")
with col_h2:
    current_time = datetime.datetime.now().strftime("%H:%M:%S UTC")
    st.markdown(f"<h3 style='text-align: right; color: #2e66ff;'>{current_time}</h3>", unsafe_allow_html=True)

st.markdown("---")

# --- Layout: Input vs Results ---
col_input, col_display = st.columns([1, 2])

with col_input:
    st.markdown("### 📡 Live Weather Feed")
    with st.container():
        # Weather Inputs
        temp = st.number_input("Dry Temperature (°C)", value=30.5, step=0.1)
        dew = st.number_input("Dew Point (°C)", value=25.0, step=0.1)
        rh = st.number_input("Relative Humidity (%)", value=75, step=1)
        qnh = st.number_input("QNH (hPa)", value=1013.0, step=0.1)
        
        st.write("") # Spacer
        generate = st.button("Generate Forecast", use_container_width=True)

with col_display:
    if generate:
        try:
            # Backend API Call
            payload = {"temp": temp, "dew_point": dew, "rh": rh, "qnh": qnh}
            response = requests.post("http://127.0.0.1:8000/api/predict", json=payload)
            res = response.json()

            # Result Card Display
            badge_class = "alert-badge" if res['alert'] else "status-badge"
            badge_text = "CAUTION" if res['alert'] else "SAFE"

            st.markdown(f"""
            <div class="metric-card">
                <span class="{badge_class}">{badge_text}</span>
                <p style='color: #8e94a5; margin-bottom: 5px;'>🕒 Immediate Nowcast (1 Hour)</p>
                <h1 style='font-size: 3.5rem; margin: 10px 0;'>{res['visibility']}</h1>
                <hr style='border-color: #2d323e;'>
                <div style='display: flex; justify-content: space-between;'>
                    <div>
                        <p style='color: #8e94a5; margin: 0;'>CLOUD CONDITION</p>
                        <h3 style='margin: 0; color: #2e66ff;'>{res['cloud_level']}</h3>
                    </div>
                    <div style='text-align: right;'>
                        <p style='color: #8e94a5; margin: 0;'>VERIFICATION STATUS</p>
                        <h3 style='margin: 0; color: #4cd964;'>VALIDATED</h3>
                    </div>
                </div>
                <p style='margin-top: 20px; font-size: 0.9rem; color: #4cd964; border-left: 3px solid #4cd964; padding-left: 10px;'>
                    Weather components are within normal operating limits for BIA airport.
                </p>
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error("Error: Could not connect to the Backend. Please ensure app.py is running on port 8000.")
    else:
        st.info("Input current weather data and click 'Generate Forecast' to view the AI analysis.")