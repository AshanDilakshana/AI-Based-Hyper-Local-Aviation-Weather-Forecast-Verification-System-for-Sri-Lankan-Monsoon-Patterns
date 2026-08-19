import joblib
import matplotlib.pyplot as plt
import pandas as pd
import os

# ================= PATH SETUP =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model_path = os.path.join(BASE_DIR, "weather_model.pkl")
features_path = os.path.join(BASE_DIR, "feature_columns.pkl")

# ================= LOAD MODEL =================
model = joblib.load(model_path)
features = joblib.load(features_path)

# ================= ORIGINAL INPUT FEATURE GROUPS =================
feature_groups = {
    "Temperature": ["temperature", "temp"],
    "Humidity": ["humidity"],
    "Pressure": ["pressure"],
    "Dew Point": ["dew_point", "dew"],
    "Wind Speed": ["wind_speed"],
    "Wind Direction": ["wind_direction", "wind_dir"],
    "Visibility": ["visibility"]
}

# ================= GROUP FEATURE IMPORTANCE FUNCTION =================
def plot_group_importance(estimator, title, save_name):

    importance = estimator.feature_importances_

    feat_imp = pd.DataFrame({
        "Feature": features,
        "Importance": importance
    })

    group_scores = {}

    for group_name, keywords in feature_groups.items():
        score = feat_imp[
            feat_imp["Feature"].str.lower().apply(
                lambda x: any(keyword in x for keyword in keywords)
            )
        ]["Importance"].sum()

        group_scores[group_name] = score

    group_df = pd.DataFrame({
        "Input Feature": list(group_scores.keys()),
        "Importance": list(group_scores.values())
    })

    group_df = group_df.sort_values(
        by="Importance",
        ascending=True
    )

    # ================= PLOT =================
    plt.figure(figsize=(10, 6))

    plt.barh(
        group_df["Input Feature"],
        group_df["Importance"],
        color="skyblue"
    )

    plt.xlabel("Importance Score")
    plt.ylabel("Input Features")
    plt.title(title)

    plt.tight_layout()

    # ================= SAVE IMAGE =================
    save_path = os.path.join(BASE_DIR, save_name)
    plt.savefig(save_path, dpi=300)

    print(f"✅ Saved: {save_path}")

    plt.show()
    plt.close()

    print("\n", title)
    print(group_df.sort_values(by="Importance", ascending=False))


# ================= TEMPERATURE FEATURE IMPORTANCE =================
plot_group_importance(
    model.estimators_[0],
    "Input Feature Importance - Temperature Prediction",
    "input_feature_importance_temperature.png"
)

# ================= PRESSURE FEATURE IMPORTANCE =================
plot_group_importance(
    model.estimators_[1],
    "Input Feature Importance - Pressure Prediction",
    "input_feature_importance_pressure.png"
)