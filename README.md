# AI-Based Hyper-Local Aviation Weather Forecast Verification System

A specialized Machine Learning-based decision support system designed for Bandaranaike International Airport (BIA), Sri Lanka. This system predicts runway-specific wind patterns during the Southwest Monsoon to enhance aviation safety and operational efficiency.

## 🚀 Key Features & Recent Upgrades

- **Hyper-Local Prediction:** Focuses specifically on BIA runway coordinates rather than broad regional forecasts.
- **Advanced Hybrid Modeling:** 
  - **1-Hour Nowcast:** High-precision short-term wind speed prediction using XGBoost.
  - **3-Hour Forecast:** Medium-term trend prediction utilizing a **Hybrid approach** combining XGBoost and **Temporal Fusion Transformers (TFT)** for maximum accuracy.
- **Automated MLOps Pipeline:** 
  - Scheduled monthly retraining of models (`scheduler.py`) to adapt to new monsoon patterns.
  - Smart live METAR data fetcher checking for new data every 32 minutes with a 48-hour backup safety net.
- **Scalable Plugin Architecture:** Backend API is built using a modular plugin design, allowing different team members (Temperature, Clouds, Visibility) to safely integrate their models without crashing the main server.
- **Safety Dashboard:** Interactive ATC-style UI with real-time **Headwind** and **Crosswind** danger level calculations.

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
  - Models: **XGBoost** (Primary), **Temporal Fusion Transformer (TFT)**, Random Forest, LSTM, and LightGBM.
  - Optimization: Hyperparameter tuning via `RandomizedSearchCV` and PyTorch Lightning.
- **Backend API (FastAPI):** High-performance REST API serving model inferences.
- **Frontend (React + Vite):** Modern dashboard for Air Traffic Controllers.

## 📊 Model Performance (3-Hour Forecast)

| Model | Architecture | Mean Absolute Error (MAE) |
| :--- | :--- | :--- |
| **XGBoost** | Gradient Boosting | **1.69 Knots** |
| **TFT_3H** | Deep Learning (Transformer) | **~1.00 Knots** |
| **Hybrid** | Ensemble (XGBoost + TFT) | **< 1.00 Knots** |

*Note: In aviation wind prediction, an MAE below 2.0 Knots is considered highly precise for operational safety.*

## 🛠️ Tech Stack

- **Data Science:** Python, Pandas, NumPy, Scikit-Learn, XGBoost, PyTorch, PyTorch Forecasting.
- **Backend:** FastAPI, Uvicorn, SQLAlchemy, APScheduler.
- **Frontend:** React.js, Vite, Tailwind CSS, Lucide Icons.

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.9+
- Node.js & npm

### 2. Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
cd backend
python main.py
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📈 Future Improvements
- **Live API Integration:** Automatic data fetching from Meteorological Department APIs *(Currently active via APScheduler)*.
- **Automated Database Logging:** Storing history for real-time lag feature calculation *(Completed)*.
- **Ensemble Stacking:** Combining multiple models for even higher accuracy *(Completed via Hybrid models)*.

## 👨‍💻 Author
**Ashan Dilakshana**
AI Developer & Researcher
