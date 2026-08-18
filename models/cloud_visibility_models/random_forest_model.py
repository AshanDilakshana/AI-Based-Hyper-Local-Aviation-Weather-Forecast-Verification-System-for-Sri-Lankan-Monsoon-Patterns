import os
import pickle

import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, r2_score
from sklearn.model_selection import train_test_split

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../'))
csv_file = os.path.join(project_root, 'data', 'aviation_weather_features.csv')

print(f"[INFO] Random Forest Script: Loading clean dataset from {csv_file}")
df = pd.read_csv(csv_file, low_memory=False)

from sklearn.preprocessing import LabelEncoder

# Target column detection
cloud_col = 'Cloud_Cleaned' if 'Cloud_Cleaned' in df.columns else 'Clouds'
vis_col = 'Visibility_Cleaned' if 'Visibility_Cleaned' in df.columns else 'Visibility'

features = ['Dry tem(0C)', 'Dew point(0C)', 'RH(%)', 'QNH (hPa)', 'Wind speed(Kts)', 'Dew_Point_Depression']
df = df.dropna(subset=features + [cloud_col, vis_col])

X = df[features]
le_cloud = LabelEncoder()
y_cloud = le_cloud.fit_transform(df[cloud_col].astype(str))
y_visibility = pd.to_numeric(df[vis_col], errors='coerce')


# Drop any rows where y_visibility became NaN after coercion
valid_mask = ~y_visibility.isna()
X = X[valid_mask]
y_cloud = y_cloud[valid_mask]
y_visibility = y_visibility[valid_mask]

save_path = os.path.abspath(os.path.join(script_dir, '../saved_models'))
os.makedirs(save_path, exist_ok=True)

# Train Standard Random Forest Cloud Model
print("[CLOUD] Training Standard Random Forest Cloud Model...")
X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, y_cloud, test_size=0.2, random_state=42)
rf_cloud = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
rf_cloud.fit(X_train_c, y_train_c)
print(f"[ACCURACY] Random Forest Cloud Accuracy: {accuracy_score(y_test_c, rf_cloud.predict(X_test_c)) * 100:.2f}%")

with open(os.path.join(save_path, 'random_forest_model.pkl'), 'wb') as f:
    pickle.dump(rf_cloud, f)

# Train Standard Random Forest Visibility Model
print("[VISIBILITY] Training Standard Random Forest Visibility Model...")
X_train_v, X_test_v, y_train_v, y_test_v = train_test_split(X, y_visibility, test_size=0.2, random_state=42)
rf_vis = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
rf_vis.fit(X_train_v, y_train_v)
print(f"[ACCURACY] Random Forest Visibility R2 Score: {r2_score(y_test_v, rf_vis.predict(X_test_v)) * 100:.2f}%")

with open(os.path.join(save_path, 'random_forest_visibility.pkl'), 'wb') as f:
    pickle.dump(rf_vis, f)

print("[SUCCESS] Random Forest Models Saved Successfully!")