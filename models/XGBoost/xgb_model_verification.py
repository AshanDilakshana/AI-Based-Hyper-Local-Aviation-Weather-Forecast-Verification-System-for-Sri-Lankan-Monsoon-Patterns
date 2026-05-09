import joblib
import os
import matplotlib.pyplot as plt
import numpy as np

# Path Logic
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def run_xgb_verification():
    try:
        model = joblib.load(os.path.join(SCRIPT_DIR, 'xgb_model.pkl'))
        X_test, y_test, _ = joblib.load(os.path.join(SCRIPT_DIR, 'xgb_test_assets.pkl'))
    except Exception as e:
        print(f"Error loading XGBoost assets: {e}")
        return

    predictions = model.predict(X_test)
    
    # 1. Comparison Table for Terminal
    print("\n" + "="*110)
    print(f"XGBOOST VERIFICATION TABLE | Researcher: P.K.V.K. Jayathilaka")
    print(f"{'No':<4} | {'Act QNH':<10} | {'AI QNH':<10} | {'Q Error':<8} | {'Act RH':<10} | {'AI RH':<10} | {'R Error':<8}")
    print("-" * 110)
    
    for i in range(15):
        act_q, pred_q = y_test.iloc[i, 0], predictions[i, 0]
        act_r, pred_r = y_test.iloc[i, 1], predictions[i, 1]
        print(f"{i+1:<4} | {act_q:<10.2f} | {pred_q:<10.2f} | {abs(act_q-pred_q):<8.2f} | {act_r:<10.1f} | {pred_r:<10.1f} | {abs(act_r-pred_r):<8.1f}")
    
    print("="*110)

    # 2. Comparison Plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # QNH Plot
    ax1.plot(y_test.iloc[:100, 0].values, label='Actual QNH', color='black', linewidth=1.5)
    ax1.plot(predictions[:100, 0], label='XGB Prediction', color='orange', linestyle='--')
    ax1.set_title('XGBoost QNH Verification')
    ax1.set_ylabel('hPa')
    ax1.legend()

    # RH Plot
    ax2.plot(y_test.iloc[:100, 1].values, label='Actual RH', color='blue', linewidth=1.5)
    ax2.plot(predictions[:100, 1], label='XGB Prediction', color='purple', linestyle='--')
    ax2.set_title('XGBoost RH Verification')
    ax2.set_ylabel('Humidity (%)')
    ax2.set_xlabel('Samples')
    ax2.legend()

    plt.tight_layout()
    save_path = os.path.join(SCRIPT_DIR, 'xgb_verification_plot.png')
    plt.savefig(save_path)
    print(f"XGBoost Verification plot saved to: {save_path}")
    plt.show()

if __name__ == "__main__":
    run_xgb_verification()