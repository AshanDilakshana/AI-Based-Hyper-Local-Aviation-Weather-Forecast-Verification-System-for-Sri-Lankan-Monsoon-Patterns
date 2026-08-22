# Thermodynamic Hazard & Aviation Performance Prediction Module
**Sub-system of the AI-Based Hyper-Local Aviation Weather Forecast Verification System for Sri Lankan Monsoon Patterns**

**Author:** Imash Sankadeepa  
**Target Airport:** Bandaranaike International Airport (VCBI), Sri Lanka  
**Monsoon Focus:** Northeast Monsoon Regime

---

## 🚀 Research Overview
This module acts as a critical independent verification layer within the broader AI aviation weather system. Rather than solely predicting standard meteorological metrics, this research focuses on the **coupled relationship between atmospheric pressure (QNH) and surface temperature**. 

By predicting these parameters 3 hours into the future (T+3) using a Hybrid Machine Learning approach, the system automatically derives critical aviation physics (Density Altitude) and acts as an early-warning trigger for Thermodynamic Hazards, specifically **Radiation Fog Precursors**.

## 🧠 Core System Capabilities

### 1. Hybrid Machine Learning Architecture
The prediction engine utilizes a sophisticated hybrid approach to maximize accuracy:
* **Random Forest Regressor:** Acts as the base model, identifying complex non-linear relationships between humidity, dew point, wind, and lag features.
* **LSTM (Long Short-Term Memory):** Handles the temporal sequencing and captures underlying time-series patterns.
* **Hybrid Integration:** The predictions from both models are fused to generate a highly stable T+3 hour prediction for Temperature and Pressure.

### 2. Live METAR Integration
The system is built for real-time operational use. It autonomously fetches live METAR strings from `aviationweather.gov`, parses raw aviation data, and feeds it directly into the AI pipeline for immediate forecasting.

### 3. Derived Aviation Physics Engine
Instead of just showing raw temperature, the system translates meteorological data into actionable aviation metrics:
* **Pressure Altitude:** Calculated using standard lapse rates.
* **ISA Temperature Deviation:** Compares predicted conditions against the International Standard Atmosphere.
* **Density Altitude:** The ultimate performance metric affecting aircraft lift and engine thrust.
* **VCBI Classification:** Categorizes density altitude specifically for Bandaranaike International Airport as `NORMAL`, `ELEVATED`, or `CRITICAL`.

### 4. Thermodynamic Hazard Precursor Verification (Novelty)
This is the core research contribution. Instead of predicting the *effect* (fog), the system predicts the *cause* (thermodynamic precursors) up to 3 hours in advance.

**The Radiation Fog Precursor Logic (Tuned for VCBI):**
Based on statistical analysis of 120,000+ historical records, the system triggers a **HIGH RISK (>85%)** alert when:
1. **Rapid Radiative Cooling:** Temperature drops by at least 1.0°C over 3 hours (Rate of Change ≤ -0.33°C/hr).
2. **High & Stable Pressure:** QNH is in the 75th percentile for VCBI (≥ 1012.0 hPa) with minimal fluctuation (≤ 0.5 hPa).

This specific coupled anomaly indicates clear skies and calm winds—the exact environment required for severe radiation fog and sudden RVR (Runway Visual Range) drops.

---

## 💻 Tech Stack & Architecture

* **Backend Engine:** FastAPI (Python)
* **Data Processing & AI:** Pandas, NumPy, Scikit-Learn, TensorFlow/Keras
* **Database:** SQLite (SQLAlchemy ORM)
* **Frontend Dashboard:** React.js, Axios, CSS3
* **Automation:** Advanced Background Scheduler for continuous METAR polling and prediction generation.

---

## 📊 Model Performance (Historical Baseline)

| Model | Accuracy (R² Score) | Mean Absolute Error (MAE) |
|---|---|---|
| Random Forest (Base) | 68% | 1.24 °C / hPa |
| LSTM (Base) | 25% | 1.92 °C / hPa |
| **Hybrid (RF + LSTM)** | **84%** | **0.86 °C / hPa** |

---

## 🎯 Contribution to the Group Project
This module perfectly complements the visual-range and cloud prediction modules handled by other team members. By isolating the thermodynamic cause (Temperature/Pressure dynamics), it functions as an independent early-warning trigger. This ensures the overall system acts as a true multi-variable "Verification System," providing Duty Forecasters and Pilots with data-driven confidence before making operational decisions.
