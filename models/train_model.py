import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import pickle
import numpy as np

# 1. Load the final processed features dataset[cite: 1]
# Using the new standard filename
df = pd.read_csv('data/aviation_weather_features.csv')

# --- Handle non-numeric data to ensure model stability ---
# Convert essential columns to numeric, replacing strings with NaN
feature_cols = ['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']
for col in feature_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Drop any rows that contain missing values after conversion
df.dropna(subset=feature_cols + ['Visibility_Status'], inplace=True)
# --------------------------------------------------------

# 2. Define Input Features (X) and Target Output (y)[cite: 1]
X = df[feature_cols]
y = df['Visibility_Status']

# 3. Split the data into Training (80%) and Testing (20%) sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Initialize and Train the Random Forest Classifier[cite: 1]
# This model is specialized for the First Inter-Monsoon detection[cite: 1]
print("Training the visibility prediction model... Please wait.")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 5. Evaluate the model accuracy
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"Model Training Complete!")
print(f"Accuracy Score: {accuracy * 100:.2f}%")
print("\nClassification Report:\n", classification_report(y_test, y_pred))

# 6. Save the trained model with a professional name[cite: 1]
with open('models/visibility_prediction_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Trained model saved as: models/visibility_prediction_model.pkl")