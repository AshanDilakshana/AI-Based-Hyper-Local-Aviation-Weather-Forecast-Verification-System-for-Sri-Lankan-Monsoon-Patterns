# Research Paper: AI-Based Hyper-Local Aviation Weather Forecast Verification System

**Author:** Ashan Dilakshana  
**Focus:** QNH, Dewpoint & Derived Relative Humidity (RH) Forecasting  
**Domain:** Aviation Meteorology, Machine Learning (LightGBM)

---

## 📄 Overview

This repository contains the codebase and methodology for the research paper focusing on predicting hyper-local atmospheric variables crucial for aviation safety at Bandaranaike International Airport (BIA), Sri Lanka. The system leverages **LightGBM** to forecast **Atmospheric Pressure (QNH)** and **Dewpoint** 3 hours into the future, and uses thermodynamic formulas (August-Roche-Magnus) to mathematically derive future **Relative Humidity (RH)**.

## 🎯 Objectives
- To predict QNH and Dewpoint 3 hours ahead using time-series tabular data.
- To eliminate the need for a separate RH machine learning model by deriving it thermodynamically.
- To deploy an automated MLOps pipeline that continuously retrains models as new meteorological data arrives.
- To establish a live verification loop that calculates the Mean Absolute Error (MAE) of forecasts against actual returning weather data.

## 🧠 Methodology & Architecture

### 1. Data Processing (`preprocessing_and_feature_engineering/`)
The data is dynamically ingested from a local SQLite database (`weather_data.db`).
- **Data Cleaner:** Handles missing values using forward-fill and back-fill logic, maintaining the sequence of time-series data.
- **Feature Engineering:** 
  - **Temporal Encoding:** Sine/Cosine transformations of UTC time to capture diurnal cycles.
  - **Temperature Spread:** Calculation of `dry_temp - dewpoint` as a key indicator for humidity/pressure shifts.
  - **Momentum & Lags:** Rolling averages (3h, 6h) and historical momentum calculations.

### 2. Predictive Engine (`Models/`)
**LightGBM Regressors** were chosen for their robust performance on tabular, non-linear atmospheric data.
- **Dewpoint Model:** High accuracy achieved (MAE ~0.58 °C) with an R-squared of ~66.7%.
- **QNH Model:** Captures macro-level atmospheric pressure shifts (MAE ~1.83 hPa) indicating passing monsoon patterns.

### 3. RH Calculation
Instead of using ML for Relative Humidity, RH is calculated directly from the predicted Dewpoint ($T_d$) and ambient Temperature ($T$):

$$ RH = 100 \times \exp\left(\frac{17.67 \times T_d}{T_d + 243.5} - \frac{17.67 \times T}{T + 243.5}\right) $$

### 4. MLOps & Verification
- **Automated Retraining:** `mlops_qnh_dewpoint_retrainer.py` ensures the AI is updated with the latest live data.
- **Live Verification (`compare_live_data.py`):** Compares predictions against ground truth upon expiration of the 3-hour forecast window, logging errors automatically.

## ⚙️ Running the Research Code

1. **Train the Models**
   ```bash
   python "Models\qnh_models\3h prediction model\train_unified_3h.py"
   python "Models\dewpoint_models\3h prediction model\train_unified_3h.py"
   ```

2. **Generate Manual 3H Predictions**
   ```bash
   python "Models\qnh_models\3h prediction model\TEST_qnh_inference.py"
   python "Models\dewpoint_models\3h prediction model\TEST_dewpoint_inference.py"
   ```

3. **Verify Predictions Against Live Data**
   ```bash
   python compare_live_data.py
   ```

## 📊 Results Summary
The hybrid approach (Machine Learning for raw variables + Thermodynamic Math for derived variables) proved highly effective. The models provide reliable, computationally efficient forecasts that are strictly bounded by meteorological physics, reducing AI hallucination risks during extreme monsoon shifts.
