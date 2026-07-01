import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier, XGBRegressor
from sklearn.metrics import accuracy_score, r2_score, mean_absolute_error
import pickle
import os

# Set file paths safely
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
csv_file = os.path.join(project_root, 'data', 'aviation_weather_features.csv')

print(f"Loading preprocessed dataset from: {csv_file}")
# low_memory=False to stop DtypeWarning completely
df = pd.read_csv(csv_file, low_memory=False)

# Features list matching your Excel columns exactly
features = ['Dry tem(0C)', 'Dew point(0C)', 'RH(%)', 'QNH (hPa)', 'Wind speed(Kts)', 'Dew_Point_Depression']
df = df.dropna(subset=features + ['Cloud_Status', 'Visibility'])

X = df[features]
y_cloud = df['Cloud_Status'].astype(int)
y_visibility = df['Visibility']

# Define a single clean directory path for models inside the main 'models' folder
save_path = os.path.join(script_dir, 'saved_models')
os.makedirs(save_path, exist_ok=True)

# -------------------------------------------------------------
# 1. CLOUD STATUS MODEL (Classification) - Target: 72%+
# -------------------------------------------------------------
print("\n Training Hyper-Tuned Cloud Status Model (XGBoost Classifier)...")
X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, y_cloud, test_size=0.2, random_state=42, stratify=y_cloud)

cloud_model = XGBClassifier(
    n_estimators=700,          # More estimators for deep patterns
    max_depth=12,              # Deep splits to capture complex monsoon conditions
    learning_rate=0.03,        # Precise steps to maximize test accuracy
    subsample=0.9,
    colsample_bytree=0.9,
    eval_metric='mlogloss',
    random_state=42,
    n_jobs=-1
)
cloud_model.fit(X_train_c, y_train_c)

cloud_acc = accuracy_score(y_test_c, cloud_model.predict(X_test_c))
print("=" * 60)
print(f" CLOUD MODEL ACCURACY: {cloud_acc * 100:.2f}%")
print("=" * 60)

# Save the cloud model in the clean folder
with open(os.path.join(save_path, 'xgb_cloud_model.pkl'), 'wb') as f:
    pickle.dump(cloud_model, f)


# 2. VISIBILITY MODEL (Regression) - Target: 72%+

print("\n👁️ Training Hyper-Tuned Visibility Model (XGBoost Regressor)...")
X_train_v, X_test_v, y_train_v, y_test_v = train_test_split(X, y_visibility, test_size=0.2, random_state=42)

visibility_model = XGBRegressor(
    n_estimators=700,
    max_depth=12,
    learning_rate=0.03,
    subsample=0.9,
    colsample_bytree=0.9,
    random_state=42,
    n_jobs=-1
)
visibility_model.fit(X_train_v, y_train_v)

vis_r2 = r2_score(y_test_v, visibility_model.predict(X_test_v))
print("=" * 60)
print(f" VISIBILITY MODEL R2 SCORE (ACCURACY): {vis_r2 * 100:.2f}%")
print(f" Visibility Mean Absolute Error: {mean_absolute_error(y_test_v, visibility_model.predict(X_test_v)):.2f} meters")
print("=" * 60)

# Save the visibility model in the clean folder
with open(os.path.join(save_path, 'xgb_visibility_model.pkl'), 'wb') as f:
    pickle.dump(visibility_model, f)

print(f"\n✅ Training Complete! Both high-accuracy models saved neatly inside: {save_path}")