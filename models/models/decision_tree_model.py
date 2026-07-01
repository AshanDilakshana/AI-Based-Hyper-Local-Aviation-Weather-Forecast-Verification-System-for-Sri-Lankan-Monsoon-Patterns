import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.metrics import accuracy_score, r2_score
import pickle
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
csv_file = os.path.join(project_root, 'data', 'aviation_weather_features.csv')

print(f"📂 Decision Tree Script: Loading clean dataset from {csv_file}")
df = pd.read_csv(csv_file, low_memory=False)

features = ['Dry tem(0C)', 'Dew point(0C)', 'RH(%)', 'QNH (hPa)', 'Wind speed(Kts)', 'Dew_Point_Depression']
df = df.dropna(subset=features + ['Cloud_Status', 'Visibility'])

X = df[features]
y_cloud = df['Cloud_Status'].astype(int)
y_visibility = df['Visibility']

save_path = os.path.join(os.path.dirname(script_dir), 'saved_models')
os.makedirs(save_path, exist_ok=True)

# Train Baseline Decision Tree Cloud Model
print("☁️ Training Baseline Decision Tree Cloud Model...")
X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, y_cloud, test_size=0.2, random_state=42)
dt_cloud = DecisionTreeClassifier(max_depth=6, random_state=42)
dt_cloud.fit(X_train_c, y_train_c)
print(f"📉 Decision Tree Cloud Accuracy: {accuracy_score(y_test_c, dt_cloud.predict(X_test_c)) * 100:.2f}%")

with open(os.path.join(save_path, 'decision_tree_cloud.pkl'), 'wb') as f:
    pickle.dump(dt_cloud, f)

# Train Baseline Decision Tree Visibility Model
print("👁️ Training Baseline Decision Tree Visibility Model...")
X_train_v, X_test_v, y_train_v, y_test_v = train_test_split(X, y_visibility, test_size=0.2, random_state=42)
dt_vis = DecisionTreeRegressor(max_depth=6, random_state=42)
dt_vis.fit(X_train_v, y_train_v)
print(f"📉 Decision Tree Visibility R2 Score: {r2_score(y_test_v, dt_vis.predict(X_test_v)) * 100:.2f}%")

with open(os.path.join(save_path, 'decision_tree_visibility.pkl'), 'wb') as f:
    pickle.dump(dt_vis, f)

print("✅ Decision Tree Models Saved Successfully!")