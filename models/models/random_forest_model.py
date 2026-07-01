import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, r2_score
import pickle
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
csv_file = os.path.join(project_root, 'data', 'aviation_weather_features.csv')

print(f"📂 Random Forest Script: Loading clean dataset from {csv_file}")
df = pd.read_csv(csv_file, low_memory=False)

features = ['Dry tem(0C)', 'Dew point(0C)', 'RH(%)', 'QNH (hPa)', 'Wind speed(Kts)', 'Dew_Point_Depression']
df = df.dropna(subset=features + ['Cloud_Status', 'Visibility'])

X = df[features]
y_cloud = df['Cloud_Status'].astype(int)
y_visibility = df['Visibility']

save_path = os.path.join(os.path.dirname(script_dir), 'saved_models')
os.makedirs(save_path, exist_ok=True)

# Train Standard Random Forest Cloud Model
print("☁️ Training Standard Random Forest Cloud Model...")
X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, y_cloud, test_size=0.2, random_state=42)
rf_cloud = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
rf_cloud.fit(X_train_c, y_train_c)
print(f"📊 Random Forest Cloud Accuracy: {accuracy_score(y_test_c, rf_cloud.predict(X_test_c)) * 100:.2f}%")

with open(os.path.join(save_path, 'random_forest_model.pkl'), 'wb') as f:
    pickle.dump(rf_cloud, f)

# Train Standard Random Forest Visibility Model
print("👁️ Training Standard Random Forest Visibility Model...")
X_train_v, X_test_v, y_train_v, y_test_v = train_test_split(X, y_visibility, test_size=0.2, random_state=42)
rf_vis = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
rf_vis.fit(X_train_v, y_train_v)
print(f"📊 Random Forest Visibility R2 Score: {r2_score(y_test_v, rf_vis.predict(X_test_v)) * 100:.2f}%")

with open(os.path.join(save_path, 'random_forest_visibility.pkl'), 'wb') as f:
    pickle.dump(rf_vis, f)

print("✅ Random Forest Models Saved Successfully!")