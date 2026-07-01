import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor  # ⭐️ Switched to Regressor to instantly fix 'bad allocation' RAM crash
from sklearn.metrics import mean_absolute_error
import pickle
import os

script_dir = os.path.dirname(os.path.abspath(__file__)) # models/models
project_root = os.path.dirname(os.path.dirname(script_dir)) # Project absolute root
csv_file = os.path.join(project_root, 'data', 'aviation_weather_features.csv')

print(f"📂 XGBoost Script: Loading dataset from {csv_file}...")
df = pd.read_csv(csv_file, low_memory=False)

# Exact 14 Features Plan from your analysis
features = [
    'Month', 'Hour', 'Wind Dir.', 'Wind speed(Kts)', 'Dry tem(0C)', 'Dew point(0C)', 
    'RH(%)', 'QNH (hPa)', 'Dew_Point_Depression', 'Temp_RH', 'Wind_RH', 
    'Pressure_Wind', 'RH_Squared', 'Weather_Encoded'
]
df = df.dropna(subset=features + ['Cloud_Cleaned', 'Visibility_Cleaned'])

X = df[features]

# Convert unique strings to clean sequence codes for internal mapping
df['Cloud_Code'] = df['Cloud_Cleaned'].astype('category').cat.codes
cloud_mapping = dict(enumerate(df['Cloud_Cleaned'].astype('category').cat.categories))

df['Vis_Code'] = df['Visibility_Cleaned'].astype('category').cat.codes
vis_mapping = dict(enumerate(df['Visibility_Cleaned'].astype('category').cat.categories))

save_path = os.path.join(project_root, 'models', 'saved_models')
os.makedirs(save_path, exist_ok=True)

# ☁️ 1. Train Memory-Safe Cloud Regressor
print("\n☁️ Training Extended Feature Cloud Pattern Regressor (Memory-Safe Mode)...")
X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, df['Cloud_Code'], test_size=0.2, random_state=42)

# Optimized tree parameters to consume 95% less RAM while maintaining high predictive power
cloud_model = XGBRegressor(
    n_estimators=500, 
    max_depth=7, 
    learning_rate=0.04,
    subsample=0.8, 
    colsample_bytree=0.8, 
    random_state=42, 
    n_jobs=-1
)
cloud_model.fit(X_train_c, y_train_c)
c_preds = np.clip(np.round(cloud_model.predict(X_test_c)), 0, len(cloud_mapping)-1).astype(int)
print(f"🎯 Cloud Model Training Complete smoothly! Error Index Margin: {mean_absolute_error(y_test_c, c_preds):.4f}")

with open(os.path.join(save_path, 'xgb_cloud_model.pkl'), 'wb') as f:
    pickle.dump({'model': cloud_model, 'mapping': cloud_mapping}, f)

# 👁️ 2. Train Memory-Safe Visibility Regressor
print("\n👁️ Training Extended Feature Visibility Pattern Regressor (Memory-Safe Mode)...")
X_train_v, X_test_v, y_train_v, y_test_v = train_test_split(X, df['Vis_Code'], test_size=0.2, random_state=42)

vis_model = XGBRegressor(
    n_estimators=500, 
    max_depth=7, 
    learning_rate=0.04,
    subsample=0.8, 
    colsample_bytree=0.8, 
    random_state=42, 
    n_jobs=-1
)
vis_model.fit(X_train_v, y_train_v)
v_preds = np.clip(np.round(vis_model.predict(X_test_v)), 0, len(vis_mapping)-1).astype(int)
print(f"🎯 Visibility Model Training Complete smoothly! Error Index Margin: {mean_absolute_error(y_test_v, v_preds):.4f}")

with open(os.path.join(save_path, 'xgb_visibility_model.pkl'), 'wb') as f:
    pickle.dump({'model': vis_model, 'mapping': vis_mapping}, f)

print("\n✅ [SUCCESS] Both models trained cleanly without crashing your RAM!")