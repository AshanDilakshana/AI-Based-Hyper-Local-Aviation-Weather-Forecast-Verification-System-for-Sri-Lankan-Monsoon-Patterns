import os
import pickle

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier, XGBRegressor


# Set file paths safely
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../'))
csv_file = os.path.join(project_root, 'data', 'aviation_weather_features.csv')

print(f"Loading preprocessed dataset from: {csv_file}")
# low_memory=False to stop DtypeWarning completely
df = pd.read_csv(csv_file, low_memory=False)

from sklearn.preprocessing import LabelEncoder

# Target column detection
cloud_col = 'Cloud_Cleaned' if 'Cloud_Cleaned' in df.columns else 'Clouds'
vis_col = 'Visibility_Cleaned' if 'Visibility_Cleaned' in df.columns else 'Visibility'

# Features list matching preprocessed data columns
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

# Define a single clean directory path for models inside main 'models/saved_models'
save_path = os.path.join(project_root, 'models', 'saved_models')
os.makedirs(save_path, exist_ok=True)

# -------------------------------------------------------------
# 1. CLOUD STATUS MODEL (Regression over Cloud Code indices)
# -------------------------------------------------------------
print("\n[CLOUD] Training Hyper-Tuned Cloud Status Model (XGBoost Regressor)...")
X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, y_cloud, test_size=0.2, random_state=42)

cloud_model = XGBRegressor(
    n_estimators=700,          # More estimators for deep patterns
    max_depth=12,              # Deep splits to capture complex monsoon conditions
    learning_rate=0.03,        # Precise steps to maximize test accuracy
    subsample=0.9,
    colsample_bytree=0.9,
    random_state=42,
    n_jobs=-1
)
cloud_model.fit(X_train_c, y_train_c)

c_preds = np.clip(np.round(cloud_model.predict(X_test_c)), 0, len(np.unique(y_cloud)) - 1).astype(int)
cloud_mae = mean_absolute_error(y_test_c, c_preds)
print("=" * 60)
print(f"[CLOUD] MODEL MAE: {cloud_mae:.4f}")
print("=" * 60)


# Save the cloud model in the clean folder
with open(os.path.join(save_path, 'xgb_cloud_model.pkl'), 'wb') as f:
    pickle.dump(cloud_model, f)


# -------------------------------------------------------------
# 2. VISIBILITY MODEL (Regression)
# -------------------------------------------------------------

print("\n[VISIBILITY] Training Hyper-Tuned Visibility Model (XGBoost Regressor)...")
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
print(f"[VISIBILITY] MODEL R2 SCORE (ACCURACY): {vis_r2 * 100:.2f}%")
print(f"[VISIBILITY] Mean Absolute Error: {mean_absolute_error(y_test_v, visibility_model.predict(X_test_v)):.2f} meters")
print("=" * 60)

# Save the visibility model in the clean folder
with open(os.path.join(save_path, 'xgb_visibility_model.pkl'), 'wb') as f:
    pickle.dump(visibility_model, f)

print(f"\n[SUCCESS] Training Complete! Both high-accuracy models saved neatly inside: {save_path}")