import pandas as pd
import pickle
import os
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '../../data/aviation_weather_features.csv')

def train_decision_tree():
    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: Data file not found at {DATA_PATH}")
        return

    df = pd.read_csv(DATA_PATH)
    
    # 1. Feature Selection
    feature_cols = ['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']
    
    # Cleaning data: Removing rows with missing values in our features and targets
    df.dropna(subset=feature_cols + ['Visibility', 'Cloud_Status'], inplace=True)

    X = df[feature_cols]
    y_vis = df['Visibility']
    y_cloud = df['Cloud_Status']

    # 2. Split Data
    X_train, X_test, y_v_train, y_v_test, y_c_train, y_c_test = train_test_split(
        X, y_vis, y_cloud, test_size=0.2, random_state=42
    )

    # 3. Training Decision Tree
    print("⏳ Training Decision Tree models...")
    dt_vis = DecisionTreeRegressor(random_state=42)
    dt_cloud = DecisionTreeClassifier(random_state=42)

    dt_vis.fit(X_train, y_v_train)
    dt_cloud.fit(X_train, y_c_train)

    # 4. Accuracy Calculation
    cloud_acc = accuracy_score(y_c_test, dt_cloud.predict(X_test)) * 100
    vis_mae = mean_absolute_error(y_v_test, dt_vis.predict(X_test))

    print("\n" + "="*40)
    print("📊 DECISION TREE RESULTS")
    print("="*40)
    print(f"✅ Cloud Accuracy: {cloud_acc:.2f}%")
    print(f"✅ Visibility MAE: {vis_mae:.2f}m")
    print("="*40)

    # Save models
    with open(os.path.join(BASE_DIR, 'decision_tree_visibility.pkl'), 'wb') as f:
        pickle.dump(dt_vis, f)
    with open(os.path.join(BASE_DIR, 'decision_tree_cloud.pkl'), 'wb') as f:
        pickle.dump(dt_cloud, f)

if __name__ == "__main__":
    train_decision_tree()