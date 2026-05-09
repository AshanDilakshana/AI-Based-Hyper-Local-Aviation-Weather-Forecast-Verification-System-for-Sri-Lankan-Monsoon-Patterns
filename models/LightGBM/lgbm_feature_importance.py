import joblib
import os
import matplotlib.pyplot as plt
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def plot_lgbm_importance():
    try:
        model = joblib.load(os.path.join(SCRIPT_DIR, 'lgbm_model.pkl'))
        _, _, features = joblib.load(os.path.join(SCRIPT_DIR, 'lgbm_test_assets.pkl'))
    except:
        print("LGBM assets missing.")
        return

    # Importance from the QNH estimator
    importances = model.estimators_[0].feature_importances_
    indices = np.argsort(importances)

    plt.figure(figsize=(10, 7))
    plt.title('LightGBM Feature Importance - BIA METAR Analysis')
    plt.barh(range(len(indices)), importances[indices], color='gold', align='center')
    plt.yticks(range(len(indices)), [features[i] for i in indices])
    plt.xlabel('Importance (Gain/Split)')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_lgbm_importance()