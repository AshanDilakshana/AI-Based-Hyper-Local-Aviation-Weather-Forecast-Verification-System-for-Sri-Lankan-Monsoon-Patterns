# AI-Based Hyper-Local Aviation Weather Forecast Verification System: QNH, Dewpoint & Relative Humidity

A comprehensive, specialized Machine Learning-based decision support system designed for Bandaranaike International Airport (BIA), Sri Lanka. This modular system predicts crucial aviation weather metrics—Atmospheric Pressure at Nautical Height (QNH), Dewpoint, and Relative Humidity—during the volatile Southwest Monsoon to enhance aviation safety and operational efficiency.

## 🚀 Key Features & Recent Upgrades

- **Hyper-Local Prediction:** Focuses specifically on BIA runway coordinates rather than broad regional forecasts.
- **Advanced Hybrid Modeling (Wind):** 
  - **1-Hour Nowcast:** High-precision short-term wind speed prediction using XGBoost.
  - **3-Hour Forecast:** Medium-term trend prediction utilizing a **Hybrid approach** combining XGBoost and **Temporal Fusion Transformers (TFT)** for maximum accuracy.
- **3-Hour Predictive Engine (QNH & Dewpoint):** Utilizes powerful **LightGBM** regressors to forecast QNH (pressure trends) and Dewpoint 3 hours into the future.
- **Dynamic RH Calculation:** Relative Humidity is dynamically and mathematically derived using the **August-Roche-Magnus formula** applied to forecasted variables, ensuring thermodynamic accuracy.
- **Automated MLOps Pipeline & Verification:** 
  - Scheduled monthly retraining of models (`scheduler.py`) to adapt to new monsoon patterns.
  - Smart live METAR data fetcher checking for new data every 32 minutes with a 48-hour backup safety net.
  - Built-in manual inference scripts (`compare_live_data.py`) to benchmark predictions against arriving real-world data seamlessly.
- **Scalable Plugin Architecture:** Backend API is built using a modular plugin design, allowing different team members (Temperature, Clouds, Visibility) to safely integrate their models without crashing the main server.
- **Safety Dashboard:** Interactive ATC-style "Glassmorphism" UI with real-time **Headwind** and **Crosswind** danger level calculations.

## 📁 Project Structure

The project has recently been restructured for better maintainability and team collaboration:

- **`/backend`**: Contains the FastAPI server, database connections, and the MLOps pipeline.
  - **`/backend/api/routers`**: Individual route handlers for different weather features (e.g., `wind_router.py`).
  - **`/backend/mlops_retrainer`**: Dedicated retraining scripts for specific models (e.g., `mlops_Wind_retrainer.py`).
  - **`scheduler.py`**: Background job scheduler for automated tasks and data fetching.
- **`/Models`**: Houses all Machine Learning models.
  - **`/Models/wind_models`**: Contains the 1H XGBoost, 3H XGBoost, and the newly added `TFT_3H` (Temporal Fusion Transformer) deep learning model.
- **`/frontend` & `/frontend 2`**: Modern "Glassmorphism" React+Vite dashboards for Air Traffic Controllers. (Currently kept local-only via .gitignore).
- **`/TEmpory`**: Contains experimental scripts like `hybrid_inference_3h.py` and Supabase live data sync utilities.

## 🏗️ System Architecture

The project is built using a decoupled modular architecture:

- **AI Engine (Python):** 
  - Models: **XGBoost** (Primary for Wind), **Temporal Fusion Transformer (TFT)**, Random Forest, LSTM, and **LightGBM** (Primary for tabular time-series).
  - Optimization: Hyperparameter tuning via `RandomizedSearchCV` and PyTorch Lightning.
  - MLOps: Automated retraining pipelines to adapt to shifting monsoon conditions.
  - Advanced Feature Engineering: Trigonometric encoding, lag calculations, temperature spreads, and rolling averages.
- **Backend API (FastAPI):** High-performance REST API serving model inferences.
- **Database:** Local SQLite (`weather_data.db`) storing both raw meteorological data and pending predictions.
- **Frontend (React + Vite):** Modern "Glassmorphism" dashboard for Air Traffic Controllers.

## 📊 Model Performance (3-Hour Forecasts)

### Wind Model Performance
| Model | Architecture | Mean Absolute Error (MAE) |
| :--- | :--- | :--- |
| **XGBoost** | Gradient Boosting | **1.69 Knots** |
| **TFT_3H** | Deep Learning (Transformer) | **~1.00 Knots** |
| **Hybrid** | Ensemble (XGBoost + TFT) | **< 1.00 Knots** |

*Note: In aviation wind prediction, an MAE below 2.0 Knots is considered highly precise for operational safety.*

### QNH & Dewpoint Model Performance
| Metric | Algorithm | Accuracy (R² Score) | Error (MAE) |
| :--- | :--- | :--- | :--- |
| **Dewpoint** | LightGBM | 66.72% | 0.58 °C |
| **QNH** | LightGBM | - | 1.83 hPa |

## 🛠️ Tech Stack

- **Data Science:** Python, Pandas, NumPy, Scikit-Learn, XGBoost, LightGBM, PyTorch, PyTorch Forecasting.
- **Backend & MLOps:** FastAPI, Uvicorn, SQLAlchemy, SQLite3, APScheduler.
- **Frontend:** React.js, Vite, Axios, Tailwind CSS, Vanilla CSS, Lucide Icons.

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
- **Live API Integration:** Automatic data fetching from Meteorological Department APIs *(Currently active via APScheduler)*.
- **Automated Database Logging:** Storing history for real-time lag feature calculation *(Completed)*.
- **Deep Learning for Pressure:** Implementing Temporal Fusion Transformers (TFT) to better capture complex non-linear QNH momentum.
- **Ensemble Stacking:** Combining multiple models for even higher accuracy across all parameters *(Completed for Wind via Hybrid models)*.

## 👨‍💻 Author
**Ashan Dilakshana** - Core System Architecture, QNH, Dewpoint, and RH forecasting modules.
