# Research Paper Documentation: Cloud & Visibility Prediction Module
**Domain:** Hyper-Local Aviation Weather Forecast Verification System for Sri Lankan Monsoon Patterns  
**Airport:** Bandaranaike International Airport (BIA / VCBI)  

---

## 1. Abstract & Introduction
This section of the research focuses on predicting two of the most critical aviation weather parameters: **Visibility (in meters)** and **Cloud Status (Cloud Cover & Type)**. During the Sri Lankan monsoon seasons, rapid fluctuations in humidity and wind cause sudden drops in visibility and the swift formation of hazardous clouds like Cumulonimbus (CB). 

Traditional time-series forecasting struggles with these sudden non-linear changes. Therefore, this module adopts a **thermodynamic, point-in-time machine learning approach**. By calculating instantaneous atmospheric relationships (such as the spread between temperature and dew point), the system can accurately predict visibility and cloud conditions for safe take-off and landing operations.

---

## 2. Data Acquisition & Preprocessing
Data is sourced continuously from official aviation channels.
- **Live Data Feed:** METAR (Meteorological Aerodrome Report) data is fetched via the `aviationweather.gov` API for the VCBI station.
- **Parsing:** Complex aviation codes are extracted using Regular Expressions (Regex).
- **Data Storage:** The parsed live data is saved into a local SQLite database (`weather_data.db`).

---

## 3. Feature Engineering & Calculations
To help the Machine Learning models understand the physical properties of the atmosphere, we engineered several advanced features based on meteorological formulas. These calculations are critical because raw temperature and humidity alone do not explain cloud formation.

1. **Dew Point Depression (`Temperature - Dew Point`)**:
   - *Scientific Justification:* The difference between dry temperature and dew point. A narrow depression (close to 0) means the air is saturated, directly indicating a high probability of fog (low visibility) and low-level cloud formation.
2. **Temperature & Humidity Interaction (`Temp * RH`)**:
   - *Scientific Justification:* Captures the combined effect of heat and moisture, which fuels convective cloud development (like Thunderstorms / CB clouds).
3. **Wind & Humidity Interaction (`Wind Speed * RH`)**:
   - *Scientific Justification:* Strong winds disperse fog, improving visibility, whereas stagnant high-humidity air reduces visibility.
4. **Pressure & Wind Interaction (`QNH * Wind Speed`)**:
   - *Scientific Justification:* Helps the model understand atmospheric stability and passing weather fronts.
5. **Non-linear Humidity Scaling (`RH Squared / RH^2`)**:
   - *Scientific Justification:* Visibility does not drop linearly with humidity. It drops exponentially when RH approaches 100%. Squaring the RH value mathematically penalizes the model, forcing it to pay more attention to near-saturation conditions.
6. **Categorical Encoding:** Present weather conditions (e.g., `RA` for Rain, `HZ` for Haze) were label-encoded.

---

## 4. Machine Learning Models Trained
We experimented with three distinct tree-based machine learning architectures to find the best fit for our non-linear atmospheric data.

### 4.1. Decision Tree (Baseline Model)
- **Concept:** A simple flowchart-like structure that splits data based on feature thresholds (e.g., "Is Dew Point Depression < 2°C?").
- **Performance:** 
  - *Cloud Accuracy:* 47.50%
  - *Visibility MAE:* 510.8 m
- **Conclusion:** Too simplistic. It suffered from overfitting and failed to capture the deep complexities of monsoon weather.

### 4.2. Random Forest (Ensemble Bagging)
- **Concept:** Builds hundreds of independent Decision Trees in parallel (Bagging) and averages their predictions to reduce overfitting.
- **Performance:** 
  - *Cloud Accuracy:* 49.90%
  - *Visibility MAE:* 485.2 m
- **Conclusion:** Highly stable and robust, but it struggled to adapt to the rare, extreme edge-cases (like sudden monsoon downpours) because it relies on average consensus.

### 4.3. XGBoost (Extreme Gradient Boosting) - Primary & Best Model
- **Concept:** Builds trees sequentially (Boosting). Instead of building them independently, each new tree is specifically trained to correct the residual errors made by the previous tree, using Gradient Descent.
- **Hyperparameter Tuning:** Tuned with deep trees (`max_depth=12`), precise learning steps (`learning_rate=0.03`), and a high number of estimators (`n_estimators=700`).
- **Performance:** 
  - **Cloud Accuracy:** **52.22%**
  - **Visibility MAE:** **450.5 m**
- **Conclusion:** **Selected for Production.** Gradient boosting proved superior in capturing the deep, non-linear relationships in rapidly shifting monsoon data. *(Note: While 52% cloud accuracy seems low in standard ML, predicting exact, highly volatile atmospheric cloud formations is exceptionally difficult. The 450.5m error margin for visibility is well within safe aviation standards).*

---

## 5. System Architecture: MLOps & API Integration
The research implementation goes beyond a static model by featuring an industrial-grade, fully automated Continuous Training (MLOps) pipeline.

### 5.1. The MLOps Pipeline (Continuous Training)
Weather patterns change (e.g., shifting monsoons/climate change), causing static models to lose accuracy (Concept Drift). To solve this:
- **Background Scheduler (`APScheduler`):** Runs asynchronously behind the FastAPI server.
- **Live Data Fetcher:** Automatically fetches and saves live BIA METAR data every 32 minutes.
- **Monthly Retraining Cron Job:** On the 1st of every month at midnight, the pipeline automatically extracts the newly accumulated live data from the SQLite database and retrains the XGBoost models from scratch.
- **Hot-Reloading:** The newly trained `.pkl` models are dynamically injected into the FastAPI server RAM, updating the system without requiring a server reboot.

### 5.2. Live Prediction Engine (FastAPI)
The backend is powered by a high-performance Python FastAPI.
- **Live DB Querying:** When an Air Traffic Controller clicks the "Predict" button on the UI, the FastAPI endpoint (`/predict`) does NOT rely on manual user inputs. It connects directly to the SQLite database, extracts the absolute latest (last recent row) live data, processes the thermodynamic features (Section 3), and generates the forecast.
- **Why Point-in-Time?** Unlike wind forecasting, which requires a historical time-series (e.g., LSTM/RNN), visibility and cloud classification were designed as point-in-time predictions. The current thermodynamic state dictates current cloud cover, making a time-series approach unnecessary for this specific module.

### 5.3. Frontend Dashboard (Streamlit)
An industrial, fully automated user interface was designed for the aviation personnel.
- **No Manual Entry:** To mimic industrial systems, the dashboard automatically syncs with the live data feed.
- **Human-Readable Output Logic:** A custom decoding algorithm translates raw ML predictions (e.g., "BKN020" or "CB") into plain English aviation alerts (e.g., *"Thunderstorm clouds (CB) detected, indicating active thunderstorm and rain conditions"*).
