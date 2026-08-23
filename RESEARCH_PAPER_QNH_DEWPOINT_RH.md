# AI-Based Hyper-Local Aviation Weather Forecast Verification System: Predicting QNH, Dewpoint, and Relative Humidity for Sri Lankan Monsoon Patterns

**Abstract**
Aviation weather forecasting demands high precision, especially for critical parameters like Atmospheric Pressure at Nautical Height (QNH), Dewpoint, and Relative Humidity (RH). This paper details the development of a localized predictive subsystem utilizing Light Gradient Boosting Machine (LightGBM) models. The system ingests hyper-local meteorological data, performs advanced feature engineering, and predicts QNH and Dewpoint 3 hours into the future. Furthermore, it mathematically derives future Relative Humidity using the August-Roche-Magnus approximation. An automated MLOps pipeline ensures continuous model retraining, while a live verification utility allows real-time accuracy benchmarking.

---

## 1. Introduction
In aviation, QNH is vital for aircraft altimeter calibration, ensuring safe separation from terrain. Dewpoint and Relative Humidity are critical indicators for fog formation, icing conditions, and overall visibility. Traditional numerical weather prediction models often lack hyper-local precision. This research addresses this gap by implementing a modular, AI-driven forecasting system specifically tuned for Sri Lankan monsoon patterns. 

## 2. Methodology

### 2.1 Data Ingestion and Preprocessing
Data is dynamically extracted from a local SQLite database (`weather_data.db`). A unified pipeline architecture was adopted, separating the preprocessing logic into distinct modules for QNH and Dewpoint. 
- **Missing Value Imputation:** Missing meteorological readings are handled using forward-fill techniques to preserve the temporal sequence.
- **Data Structuring:** Time-series data is chronologically sorted to prevent data leakage during model training.

### 2.2 Feature Engineering
Advanced feature engineering was crucial for capturing atmospheric dynamics:
1. **Temporal Encoding:** The time of day is cyclically encoded using sine and cosine transformations (`hour_sin`, `hour_cos`) to capture diurnal atmospheric rhythms.
2. **Temperature Spread:** The difference between dry air temperature and dewpoint (`temp_spread`) is calculated, serving as a strong predictor for humidity and pressure shifts.
3. **Momentum and Lags:** Historical time-steps (`lag_1`, `lag_2`) and momentum (current value minus previous value) were introduced for QNH to help the algorithm detect pressure trends.
4. **Rolling Averages:** 3-hour and 6-hour rolling means smoothen short-term fluctuations, exposing macro-level weather patterns.

### 2.3 Machine Learning Architecture
**LightGBM (Light Gradient Boosting Machine)** was selected as the core regression engine due to its efficiency with tabular time-series data and robust handling of non-linear relationships.
- The models were trained to predict a target shifted 3 hours into the future.
- The dataset was split chronologically (80% training, 20% testing) without shuffling to maintain time-series integrity.

### 2.4 Relative Humidity (RH) Calculation
Instead of training an independent machine learning model for Relative Humidity, the system derives RH using the highly accurate **August-Roche-Magnus (Magnus-Tetens) formula**.
By predicting the Dewpoint ($T_d$) 3 hours ahead and cross-referencing it with ambient temperature predictions ($T$), the RH is calculated as:
$$ RH = 100 \times \exp\left(\frac{17.67 \times T_d}{T_d + 243.5} - \frac{17.67 \times T}{T + 243.5}\right) $$
This hybrid approach reduces computational overhead and maintains thermodynamic consistency between forecasted variables.

---

## 3. System Architecture & MLOps

### 3.1 Automated Retraining (MLOps)
To adapt to changing monsoon patterns, a dedicated MLOps module (`mlops_qnh_dewpoint_retrainer.py`) was developed. This script automatically re-extracts the latest database records, passes them through the unified pipelines, and retrains the LightGBM models. 

### 3.2 Live Data Verification
A manual inference and verification subsystem was built to test model accuracy against real-world conditions. 
- **Inference Scripts:** `TEST_qnh_inference.py` and `TEST_dewpoint_inference.py` generate 3-hour forecasts based on the latest available data.
- **Verification Engine:** `compare_live_data.py` continuously scans pending predictions. Once the target time arrives and actual data is ingested into the database, it calculates the Mean Absolute Error (MAE) and outputs a comparative report.

---

## 4. Results & Evaluation
The models were evaluated using R-squared ($R^2$), Mean Absolute Error (MAE), and Root Mean Squared Error (RMSE).

- **Dewpoint 3H Forecast:** Demonstrated strong predictive capability with an $R^2$ of ~0.66 and an MAE of ~0.58 °C. This high accuracy directly contributes to the precision of the derived Relative Humidity calculations.
- **QNH 3H Forecast:** Proved more challenging due to the highly volatile nature of hyper-local atmospheric pressure during monsoon shifts. While the MAE remained acceptable for operational guidelines (~1.8 hPa), further deep-learning architectures (e.g., Temporal Fusion Transformers) are recommended for capturing complex pressure momentum.

## 5. Conclusion
This subsystem successfully demonstrates a modular, scalable approach to hyper-local aviation weather forecasting. By combining robust feature engineering, efficient gradient boosting (LightGBM), and established thermodynamic formulas (Magnus approximation), the system provides reliable 3-hour predictions for Dewpoint and derived Relative Humidity. The integrated MLOps and live-verification tools ensure the system remains dynamically responsive to Sri Lanka's unique weather patterns.
