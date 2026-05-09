import pandas as pd
import joblib
import os
import matplotlib.pyplot as plt
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def plot_importance():
    try:
        model = joblib.load(os.path.join(SCRIPT_DIR, 'rf_model.pkl'))
        _, _, features = joblib.load(os.path.join(SCRIPT_DIR, 'rf_test_assets.pkl'))
    except Exception as e:
        print(f"Error loading model: {e}. Run rf_model_training.py first.")
        return

    # Extract feature importance from the QNH estimator (first target)
    importances = model.estimators_[0].feature_importances_
    indices = np.argsort(importances)

    plt.figure(figsize=(10, 6))
    plt.title('Feature Importances for Weather Prediction (QNH)')
    plt.barh(range(len(indices)), importances[indices], color='skyblue', align='center')
    plt.yticks(range(len(indices)), [features[i] for i in indices])
    plt.xlabel('Relative Importance Weight')
    plt.tight_layout()
    
    save_path = os.path.join(SCRIPT_DIR, 'feature_importance.png')
    plt.savefig(save_path)
    plt.show()
    print(f"Success: Feature Importance plot saved to {save_path}")

if __name__ == "__main__":
    plot_importance()