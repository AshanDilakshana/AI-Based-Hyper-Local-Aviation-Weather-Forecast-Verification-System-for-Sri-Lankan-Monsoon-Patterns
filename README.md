AI-Based Hyper-Local Aviation Weather Forecast Verification System
Module
Cloud Status & Visibility Verification Engine

A Machine Learning-based verification and decision support system developed for Bandaranaike International Airport.

This module focuses on predicting and verifying:

Visibility
Cloud Status

during the First Inter-Monsoon period to support safer flight take-off operations.

🚀 Key Features
Hyper-Local Verification
Monitors BIA runway weather conditions
Compares predicted weather with actual METAR observations
Take-off Safety Focus
Detects dangerous low-visibility conditions
Monitors cloud base height below 5,000 ft
Automated Label Verification
Verifies AI-predicted cloud categories:
FEW
SCT
BKN
OVC
Advanced Feature Engineering
Dew Point Depression calculation for fog and cloud prediction
METAR categorical encoding for AI processing

System Architecture
AI Engine (Python)
Models Used
Random Forest (Primary Model)
XGBoost
Decision Tree

Main Functions
Data preprocessing
Dew Point Depression calculation
Label encoding
Visibility & cloud verification
📊 Model Performance
Model	Cloud Accuracy	Visibility MAE	Status
Random Forest	52.22%	450.5m	Best Performing
XGBoost	49.90%	485.2m	Moderate
Decision Tree	47.50%	510.8m	Average
Note

Cloud prediction is difficult during rapid monsoon weather changes, but visibility prediction within 500m is important for aviation safety.

Tech Stack

Python
Pandas
NumPy
Scikit-Learn
XGBoost

Research Focus
METAR data analysis (2019–2024)


📈 Future Improvements
* Live METAR and TAF data integration
* Real-time cloud and visibility verification
* Automated weather data storage system
* Improved prediction accuracy using new datasets
* Prediction of additional aviation weather parameters
* Continuous model retraining through data pipeline
* Better support for safer flight take-off operations

👨‍💻 Author
Sachinthika Jayawardhana 
AI Developer & Researcher