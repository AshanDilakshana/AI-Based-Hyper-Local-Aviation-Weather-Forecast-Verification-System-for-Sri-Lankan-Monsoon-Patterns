import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import pickle
import os

# Create models directory if it doesn't exist
if not os.path.exists('models'):
    os.makedirs('models')

# Load dataset
df = pd.read_csv('../data/aviation_weather_features.csv')
df.replace("No data", np.nan, inplace=True)

# Clean numeric columns
cols = ['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']
for col in cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df['Visibility'] = pd.to_numeric(df['Visibility'], errors='coerce')
df.dropna(subset=cols + ['Visibility'], inplace=True)

X = df[cols]
y = df['Visibility']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Training Regressor for numerical visibility values
model = RandomForestRegressor(n_estimators=500, max_depth=20, random_state=42)
model.fit(X_train, y_train)

# Save visibility model
with open('visibility_prediction_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Success: Visibility model trained and saved in models/ folder.")