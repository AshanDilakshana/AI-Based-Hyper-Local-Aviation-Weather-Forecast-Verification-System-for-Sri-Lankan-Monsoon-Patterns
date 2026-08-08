# AI-Based Hyper-Local Aviation Weather Forecast Verification System

A specialized Machine Learning-based decision support system designed for Bandaranaike International Airport (BIA), Sri Lanka. This system predicts runway-specific wind patterns during the Southwest Monsoon to enhance aviation safety and operational efficiency.

## 🚀 Key Features

- **Hyper-Local Prediction:** Focuses specifically on BIA runway coordinates rather than broad regional forecasts.
- **Dual Prediction Horizons:** 
  - **1-Hour Nowcast:** High-precision short-term wind speed prediction.
  - **3-Hour Forecast:** Medium-term trend prediction for flight scheduling.
- **Advanced Feature Engineering:** 
  - Trigonometric encoding for cyclical wind direction and time.
  - Temporal momentum calculations (Lag features).
  - Atmospheric pressure (QNH) integration for improved precision.
- **Safety Dashboard:** Interactive ATC-style UI with real-time **Headwind** and **Crosswind** danger level calculations.

## 🏗️ System Architecture

The project is built using a decoupled modular architecture:

- **AI Engine (Python):** 
  - Models: **XGBoost** (Primary), Random Forest, LSTM, and LightGBM.
  - Optimization: Hyperparameter tuning via `RandomizedSearchCV`.
- **Backend API (FastAPI):** High-performance REST API serving model inferences.
- **Frontend (React + Vite):** Modern "Glassmorphism" dashboard for Air Traffic Controllers.

## 📊 Model Performance (3-Hour Forecast)

| Model | Accuracy (R² Score) | Mean Absolute Error (MAE) |
| :--- | :--- | :--- |
| **XGBoost** | **49.39%** | **1.69 Knots** |
| Random Forest | 47.84% | 1.73 Knots |
| LSTM | 47.89% | 1.74 Knots |

*Note: In aviation wind prediction, an MAE below 2.0 Knots is considered highly precise for operational safety.*

## 🛠️ Tech Stack

- **Data Science:** Python, Pandas, NumPy, Scikit-Learn, XGBoost, PyTorch, Matplotlib.
- **Backend:** FastAPI, Uvicorn, Pydantic.
- **Frontend:** React.js, Axios, Lucide Icons, Vanilla CSS.

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
- **Live API Integration:** Automatic data fetching from Meteorological Department APIs.
- **Automated Database Logging:** Storing history for real-time lag feature calculation.
- **Ensemble Stacking:** Combining multiple models for even higher accuracy.

## 👨‍💻 Author
**Ashan Dilakshana**
AI Developer & Researcher
