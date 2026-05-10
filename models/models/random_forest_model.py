import pandas as pd
import pickle
import os
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error

# 1. Path Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '../../data/aviation_weather_features.csv')
MODEL_SAVE_PATH = BASE_DIR 

def train_random_forest_stable():
    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: Data file not found at {DATA_PATH}")
        return

    print("📂 Loading Data and applying Stable Tuning...")
    df = pd.read_csv(DATA_PATH)
    
    feature_cols = ['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']
    df.dropna(subset=feature_cols + ['Visibility', 'Cloud_Status'], inplace=True)

    X = df[feature_cols]
    y_vis = df['Visibility']
    y_cloud = df['Cloud_Status']

    # 2. Split Data 
    # test_size එක 0.2 ම තියමු, stratify අයින් කරලා බලමු සමහරවිට ඒකෙන් accuracy එක වැඩි වෙන්න පුළුවන්
    X_train, X_test, y_v_train, y_v_test, y_c_train, y_c_test = train_test_split(
        X, y_vis, y_cloud, test_size=0.2, random_state=42
    )

    # 3. Training with Balanced Parameters (To beat XGBoost)
    print("⏳ Training Stable Random Forest Models...")
    
    # පරාමිතීන් ඕනෑවට වඩා වැඩි නොකර මධ්‍යම මට්ටමක තබා ගැනීම
    cloud_model = RandomForestClassifier(
        n_estimators=200,        # ගස් ගණන සාමාන්‍ය මට්ටමකට ගෙනාවා
        max_depth=15,            # Depth එක 15 ට සීමා කළා Overfitting නවත්වන්න
        min_samples_split=5,     # පොඩි වෙනස්කම් වලට ඕනෑවට වඩා අවධානය දීම නැවැත්වුවා
        random_state=42,
        n_jobs=-1
    )
    
    vis_model = RandomForestRegressor(
        n_estimators=200, 
        max_depth=15, 
        random_state=42, 
        n_jobs=-1
    )

    cloud_model.fit(X_train, y_c_train)
    vis_model.fit(X_train, y_v_train)

    # 4. Accuracy Calculation
    cloud_acc = accuracy_score(y_c_test, cloud_model.predict(X_test)) * 100
    vis_mae = mean_absolute_error(y_v_test, vis_model.predict(X_test))

    print("\n" + "="*40)
    print("📊 STABLE RANDOM FOREST RESULTS")
    print("="*40)
    print(f"✅ Cloud Accuracy: {cloud_acc:.2f}%")
    print(f"✅ Visibility MAE: {vis_mae:.2f} m")
    print("="*40)

    # 5. Save models
    with open(os.path.join(MODEL_SAVE_PATH, 'random_forest_visibility.pkl'), 'wb') as f:
        pickle.dump(vis_model, f)
    with open(os.path.join(MODEL_SAVE_PATH, 'random_forest_cloud.pkl'), 'wb') as f:
        pickle.dump(cloud_model, f)

if __name__ == "__main__":
    train_random_forest_stable()