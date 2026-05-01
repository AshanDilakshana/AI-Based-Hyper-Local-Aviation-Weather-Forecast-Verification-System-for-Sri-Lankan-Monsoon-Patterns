import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import pickle
import numpy as np

# 1. Load the processed dataset
df = pd.read_csv('data/aviation_weather_features.csv')

# --- NEW: Aggressive cleaning of non-numeric data ---
# List of all columns used for training
feature_cols = ['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']
target_col = 'Cloud_Level'

# Convert features and target to numeric, forcing 'No data' to NaN
for col in feature_cols + [target_col]:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Drop any rows that contain NaN in features or the target
df.dropna(subset=feature_cols + [target_col], inplace=True)
# ---------------------------------------------------

# 2. Define Input Features (X) and Target (y)
X = df[feature_cols]
y = df[target_col]

# 3. Split the data (80% Training, 20% Testing)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Initialize and Train the Random Forest Model[cite: 1]
print("Training the Cloud Prediction Model... Please wait.")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 5. Evaluate accuracy
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Cloud Model Accuracy: {accuracy * 100:.2f}%")

# 6. Save the trained model with a professional name[cite: 1]
with open('models/cloud_prediction_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Cloud Prediction Model saved as: models/cloud_prediction_model.pkl")