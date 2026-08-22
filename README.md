# AI-Based Hyper-Local Aviation Weather Forecast Verification System: QNH, Dewpoint & Relative Humidity

A comprehensive, specialized Machine Learning-based decision support system designed for Bandaranaike International Airport (BIA), Sri Lanka. This modular system predicts crucial aviation weather metrics—Atmospheric Pressure at Nautical Height (QNH), Dewpoint, and Relative Humidity—during the volatile Southwest Monsoon to enhance aviation safety and operational efficiency.

## 🚀 Key Features

- **Unified Pipeline Architecture:** Dedicated, robust data preprocessing and feature extraction directly from a live SQLite database.
- **3-Hour Predictive Engine:** Utilizes powerful **LightGBM** regressors to forecast QNH (pressure trends) and Dewpoint 3 hours into the future.
- **Dynamic RH Calculation:** Rather than an isolated ML model, Relative Humidity is dynamically and mathematically derived using the **August-Roche-Magnus formula** applied to 3-hour forecasted variables, ensuring thermodynamic accuracy.
- **Live Verification System:** Built-in manual inference scripts (`compare_live_data.py`) to benchmark predictions against arriving real-world data seamlessly.

## 🏗️ System Architecture

The project is built using a decoupled modular architecture:

- **AI Engine (Python):** 
  - Models: **LightGBM** (Primary for tabular time-series).
  - MLOps: Automated retraining pipelines (`mlops_qnh_dewpoint_retrainer.py`) to adapt to shifting monsoon conditions.
  - Advanced Feature Engineering: Trigonometric encoding, lag calculations, temperature spreads, and rolling averages.
- **Backend API (FastAPI):** High-performance REST API serving model inferences.
- **Database:** Local SQLite (`weather_data.db`) storing both raw meteorological data and pending predictions.
- **Frontend (React + Vite):** Modern "Glassmorphism" dashboard for Air Traffic Controllers.

## 📊 Model Performance (3-Hour Forecasts)

| Metric | Algorithm | Accuracy (R² Score) | Error (MAE) |
| :--- | :--- | :--- | :--- |
| **Dewpoint** | LightGBM | 66.72% | 0.58 °C |
| **QNH** | LightGBM | - | 1.83 hPa |

## 🛠️ Tech Stack

- **Data Science:** Python, Pandas, NumPy, Scikit-Learn, LightGBM, PyTorch.
- **Backend / MLOps:** FastAPI, Uvicorn, SQLite3.
- **Frontend:** React.js, Axios, Lucide Icons, Vanilla CSS.

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.9+
- Node.js & npm

### 2. Backend & AI Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
cd backend
python main.py
```

### 3. Model Testing & Live Verification (QNH & Dewpoint)
```bash
# Generate a manual 3-hour forecast
python "Models\qnh_models\3h prediction model\TEST_qnh_inference.py"
python "Models\dewpoint_models\3h prediction model\TEST_dewpoint_inference.py"

# Verify predictions against live data
python compare_live_data.py

# Auto-Retrain models (MLOps)
python backend\mlops_retrainer\mlops_qnh_dewpoint_retrainer.py
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📈 Future Improvements
- **Live API Integration:** Automatic data fetching from Meteorological Department APIs.
- **Deep Learning for Pressure:** Implementing Temporal Fusion Transformers (TFT) to better capture complex non-linear QNH momentum.
- **Ensemble Stacking:** Combining multiple models for even higher accuracy across all parameters.

## 👨‍💻 Author
**Ashan Dilakshana** - Core System Architecture, QNH, Dewpoint, and RH forecasting modules.
