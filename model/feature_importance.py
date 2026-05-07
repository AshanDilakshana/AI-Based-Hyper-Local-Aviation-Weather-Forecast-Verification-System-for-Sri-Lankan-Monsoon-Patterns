import joblib
import matplotlib.pyplot as plt
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model_path = os.path.join(BASE_DIR, "weather_model.pkl")
features_path = os.path.join(BASE_DIR, "feature_columns.pkl")

model = joblib.load(model_path)
features = joblib.load(features_path)

target_names = ["Temperature", "Pressure"]

def plot_importance(estimator, title, save_name):
    importance = estimator.feature_importances_

    feat_imp = pd.DataFrame({
        "Feature": features,
        "Importance": importance
    })

    feat_imp = feat_imp.sort_values(by="Importance", ascending=True)

    plt.figure(figsize=(10, 6))
    plt.barh(feat_imp["Feature"], feat_imp["Importance"], color="skyblue")
    plt.xlabel("Importance Score")
    plt.title(title)
    plt.tight_layout()

    save_path = os.path.join(BASE_DIR, save_name)
    plt.savefig(save_path, dpi=300)
    print(f"✅ Saved: {save_path}")

    plt.show()
    plt.close()

plot_importance(
    model.estimators_[0],
    "Feature Importance - Temperature Prediction",
    "feature_importance_temperature.png"
)

plot_importance(
    model.estimators_[1],
    "Feature Importance - Pressure Prediction",
    "feature_importance_pressure.png"
)