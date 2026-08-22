# AI-Based Hyper-Local Aviation Weather Forecast Verification System: Predicting QNH, Dewpoint, and Relative Humidity for Sri Lankan Monsoon Patterns

**Abstract**
Aviation weather forecasting demands high precision, especially for critical parameters like Atmospheric Pressure at Nautical Height (QNH), Dewpoint, and Relative Humidity (RH). This paper details the development of a localized predictive subsystem utilizing Light Gradient Boosting Machine (LightGBM) models. The system dynamically ingests hyper-local meteorological data from a live SQLite database, performs advanced feature engineering in real-time, and predicts QNH and Dewpoint 3 hours into the future. Furthermore, it mathematically derives future Relative Humidity using the August-Roche-Magnus approximation. The architecture is fully decoupled to merge seamlessly with a broader team master project, featuring an automated MLOps background scheduler for continuous model retraining, and a live RESTful API for inference.

---

## 1. Introduction
In aviation, QNH is vital for aircraft altimeter calibration, ensuring safe separation from terrain. Dewpoint and Relative Humidity are critical indicators for fog formation, icing conditions, and overall visibility. Traditional numerical weather prediction models often lack hyper-local precision. This research addresses this gap by implementing a modular, AI-driven forecasting system specifically tuned for Sri Lankan monsoon patterns, designed to plug into a larger multi-model aviation API framework.

## 2. Methodology

### 2.1 Live Data Ingestion and Preprocessing
Data is dynamically extracted from a local SQLite database (`weather_data.db`). A unified pipeline architecture was adopted, separating the preprocessing logic into distinct modules for QNH and Dewpoint. 
- **Database Integration:** The system reads directly from the live database during inference to ensure models always predict on the most up-to-date atmospheric conditions.
- **Missing Value Imputation:** Missing meteorological readings are handled using forward-fill and back-fill techniques to preserve temporal continuity.

### 2.2 Dynamic Feature Engineering
Advanced feature engineering was crucial for capturing atmospheric dynamics. The `unified_pipeline.py` calculates these features on-the-fly during both training and real-time API inference:
1. **Temporal Encoding:** The time of day is cyclically encoded using sine and cosine transformations (`hour_sin`, `hour_cos`) to capture diurnal atmospheric rhythms.
2. **Temperature Spread:** The difference between dry air temperature and dewpoint (`temp_spread`) is calculated, serving as a strong predictor for humidity and pressure shifts.
3. **Momentum and Lags:** Historical time-steps (`lag_1`, `lag_2`, `lag_3`) and momentum (current value minus previous value) were introduced to help the algorithm detect pressure trends.
4. **Rolling Averages:** 3-hour and 6-hour rolling means and standard deviations smooth out short-term fluctuations, exposing macro-level weather patterns. During live inference, the pipeline dynamically calculates these moving averages using recent historical data from the database before passing the final row to the model.

### 2.3 Machine Learning Architecture
**LightGBM (Light Gradient Boosting Machine)** was selected as the core regression engine due to its efficiency with tabular time-series data and robust handling of non-linear relationships.
- The models predict a target shifted 3 hours into the future.
- The dataset was split chronologically (80% training, 20% testing) without shuffling to maintain time-series integrity.

### 2.4 Relative Humidity (RH) Calculation & Model Integration
Instead of training an independent machine learning model for Relative Humidity, the system derives RH using the highly accurate **August-Roche-Magnus (Magnus-Tetens) formula**.
By predicting the Dewpoint ($T_d$) 3 hours ahead, it cross-references it with ambient temperature predictions ($T$) to calculate RH:
$$ RH = 100 \times \exp\left(\frac{17.67 \times T_d}{T_d + 243.5} - \frac{17.67 \times T}{T + 243.5}\right) $$
*Integration Note:* The calculation is designed to ingest future temperature predictions from an external sub-model developed in parallel. Until integration, the formula dynamically proxies the current live temperature.

---

## 3. System Architecture & MLOps

The subsystem's architecture was meticulously decoupled to align with the main project's master branch.

### 3.1 RESTful API Gateway (`main.py` & `qnh_dewpoint_router.py`)
A dedicated FastAPI router was built to serve inference requests. When the `/predict/3h` endpoint is triggered, it automatically connects to the SQLite database, runs the unified preprocessing pipeline to generate time-series features (averages and lags), extracts the most recent row, and executes the LightGBM models.

### 3.2 Automated Retraining via Background Scheduler (`scheduler.py`)
To adapt to changing monsoon patterns, a dedicated MLOps module (`mlops_qnh_dewpoint_retrainer.py`) was developed. An `APScheduler` background job runs systematically to trigger retraining:
- Extracts the latest database records.
- Passes them through the training pipeline to calculate shifted future targets.
- Retrains the LightGBM models.
- Hot-reloads the updated AI models directly into the running FastAPI RAM without system downtime.

### 3.3 Live Data Verification
A verification subsystem (`compare_live_data.py`) was built to test model accuracy against real-world conditions continuously. It scans pending predictions, and once the 3-hour target time arrives and actual data is ingested into the database, it calculates the Mean Absolute Error (MAE) and outputs a comparative report.

---

## 4. Results & Evaluation
The models were evaluated using R-squared ($R^2$), Mean Absolute Error (MAE), and Root Mean Squared Error (RMSE).

- **Dewpoint 3H Forecast:** Demonstrated strong predictive capability with an $R^2$ of ~0.66 and an MAE of ~0.58 °C. This high accuracy directly contributes to the precision of the derived Relative Humidity calculations.
- **QNH 3H Forecast:** Proved more challenging due to the highly volatile nature of hyper-local atmospheric pressure during monsoon shifts. While the MAE remained acceptable for operational guidelines (~1.8 hPa), further deep-learning architectures are recommended for capturing complex pressure momentum.

## 5. Conclusion
This subsystem successfully demonstrates a modular, scalable approach to hyper-local aviation weather forecasting. By combining robust feature engineering, efficient gradient boosting (LightGBM), and established thermodynamic formulas (Magnus approximation), the system provides reliable 3-hour predictions for Dewpoint and derived Relative Humidity. The automated live database API, background MLOps retraining scheduler, and live-verification tools ensure the system remains dynamically responsive to Sri Lanka's unique weather patterns and seamlessly integrates into the broader multi-team aviation architecture.
