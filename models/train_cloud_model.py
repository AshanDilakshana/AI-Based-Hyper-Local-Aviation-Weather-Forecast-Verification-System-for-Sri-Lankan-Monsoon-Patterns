import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle

# 1. Load the data
df = pd.read_csv('data/aviation_weather_features.csv')

# 2. Data Cleaning: 
# Replace string "No data" with actual NaN (Not a Number)
df.replace("No data", np.nan, inplace=True)

# Drop rows that have any NaN values to keep the data clean
df.dropna(inplace=True)

# Ensure all feature columns are numeric
cols_to_fix = ['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']
for col in cols_to_fix:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Drop any new NaNs created during conversion
df.dropna(inplace=True)

# 3. Features and Target
X = df[['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']]
y = df['Cloud_Level']

# 4. Train Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5. Using Random Forest for better results
model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
model.fit(X_train, y_train)

# 6. Save the model
with open('models/cloud_prediction_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Model trained successfully after cleaning 'No data' values!")