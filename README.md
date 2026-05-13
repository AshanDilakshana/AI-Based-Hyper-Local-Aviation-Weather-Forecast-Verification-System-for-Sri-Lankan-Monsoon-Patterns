# AI-Based Hyper-Local Aviation Weather Forecast Verification System for Sri Lankan Monsoon Patterns

A Machine Learning-based aviation weather forecast verification system developed for Bandaranaike International Airport (BIA), Sri Lanka.  
This research focuses on predicting critical aviation weather parameters such as Dry temperature and  pressure using historical METAR weather data to support accurate aviation weather forecasting during Sri Lankan monsoon conditions.

---

# 🚀 Key Features

### Hyper-Local Aviation Weather Analysis
Focused specifically on Bandaranaike International Airport (BIA) weather conditions rather than broad regional forecasting.

### Aviation Weather Prediction
Predicts important aviation weather parameters including:
- Dry Temperature
- Pressure (QNH)

### Multi-Parameter Input Features
Uses multiple atmospheric parameters for prediction:
- Humidity
- Dew Point
- Wind Speed
- Wind Direction
- Visibility
- Pressure
- Temperature

### Advanced Feature Engineering
Implemented:
- Lag Features
- Rolling Average Features
- Time-Based Features
- Weather Relationship-Based Features

### Forecast Verification Support
Supports comparison between predicted weather conditions and actual METAR observations.

---

# 🏗️ System Architecture

## AI Engine (Python)

Responsible for:
- Data preprocessing
- Feature engineering
- Model training
- Prediction generation

### Machine Learning Models
- Random Forest
- LSTM
- Autoencoder

---

## Backend System

Built using Flask API for serving trained machine learning model predictions.

---

## Frontend Dashboard

Developed using React.js for:
- Weather parameter input
- Prediction visualization
- Forecast verification support

---
## 📊 Model Performance

| Model | Accuracy (R² Score) | Mean Absolute Error (MAE) |
|---|---|---|
| Random Forest | 68% | 1.24 |
| LSTM | 25% | 1.39 |
| Autoencoder | 45% | 1.51 |

> Note: Random Forest achieved the best performance for aviation weather parameter prediction.
---

# 🛠️ Technologies Used

## Data Science & AI
- Python
- Pandas
- NumPy
- Scikit-Learn
- TensorFlow/Keras
- Matplotlib
- Joblib

## Backend
- Flask

## Frontend
- React.js
- Axios
- CSS

---

# ⚙️ Future Improvements

- Live METAR data integration
- Real-time forecast verification
- Automated database logging
- Improved model accuracy
- Additional aviation weather parameter prediction

---

# 👩‍💻 Author

Imash Sankadeepa
Undergraduate Research Project  
AI-Based Aviation Weather Forecast Verification System