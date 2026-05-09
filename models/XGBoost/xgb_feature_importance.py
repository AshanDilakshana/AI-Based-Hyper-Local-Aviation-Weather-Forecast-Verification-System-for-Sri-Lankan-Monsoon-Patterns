import joblib
import os
import matplotlib.pyplot as plt
import numpy as np

# Path Logic
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def plot_xgb_importance():
    try:
        # Load XGBoost specific assets
        model = joblib.load(os.path.join(SCRIPT_DIR, 'xgb_model.pkl'))
        _, _, features = joblib.load(os.path.join(SCRIPT_DIR, 'xgb_test_assets.pkl'))
    except Exception as e:
        print(f"Error: Could not find XGBoost assets. {e}")
        return

    # Extract importance from the first target (QNH)
    importances = model.estimators_[0].feature_importances_
    indices = np.argsort(importances)

    plt.figure(figsize=(10, 7))
    plt.title('XGBoost Feature Importance Analysis - P.K.V.K. Jayathilaka')
    plt.barh(range(len(indices)), importances[indices], color='teal', align='center')
    plt.yticks(range(len(indices)), [features[i] for i in indices])
    plt.xlabel('F-Score (Importance)')
    plt.grid(axis='x', linestyle='--', alpha=0.6)
    plt.tight_layout()
    
    save_path = os.path.join(SCRIPT_DIR, 'xgb_feature_importance.png')
    plt.savefig(save_path)
    print(f"XGBoost Importance Plot saved to: {save_path}")
    plt.show()

if __name__ == "__main__":
    plot_xgb_importance()