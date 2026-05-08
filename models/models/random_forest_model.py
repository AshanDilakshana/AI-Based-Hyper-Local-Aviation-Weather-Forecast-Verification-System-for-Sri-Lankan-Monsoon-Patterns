import pandas as pd
import pickle
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score

# 1. Load the takeoff-focused dataset
df = pd.read_csv('../../data/aviation_weather_features.csv')

# 2. Handle non-numeric data and 'No data' values
feature_cols = ['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']
for col in feature_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Drop rows with NaN values after conversion
df.dropna(subset=feature_cols + ['Visibility', 'Visibility_Status'], inplace=True)

X = df[feature_cols]
y_vis = df['Visibility']
y_cloud = df['Visibility_Status']

# 3. Split data
X_train, X_test, y_v_train, y_v_test, y_c_train, y_c_test = train_test_split(
    X, y_vis, y_cloud, test_size=0.2, random_state=42
)

# 4. Train Models
vis_model = RandomForestRegressor(n_estimators=100, random_state=42)
vis_model.fit(X_train, y_v_train)

cloud_model = RandomForestClassifier(n_estimators=100, random_state=42)
cloud_model.fit(X_train, y_c_train)

# 5. Evaluation
v_preds = vis_model.predict(X_test)
c_preds = cloud_model.predict(X_test)
print(f"Random Forest - Visibility MAE: {mean_absolute_error(y_v_test, v_preds)}")
print(f"Random Forest - Cloud Accuracy: {accuracy_score(y_c_test, c_preds) * 100:.2f}%")

# 6. Save models
with open('random_forest_visibility.pkl', 'wb') as f:
    pickle.dump(vis_model, f)
with open('random_forest_cloud.pkl', 'wb') as f:
    pickle.dump(cloud_model, f)

print("Random Forest models saved successfully!")