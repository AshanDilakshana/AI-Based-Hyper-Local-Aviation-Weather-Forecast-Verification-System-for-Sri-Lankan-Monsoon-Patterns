import joblib
import os
import matplotlib.pyplot as plt
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def run_verification():
    try:
        # Load the saved model and test assets
        model = joblib.load(os.path.join(SCRIPT_DIR, 'rf_model.pkl'))
        X_test, y_test, _ = joblib.load(os.path.join(SCRIPT_DIR, 'rf_test_assets.pkl'))
    except Exception as e:
        print(f"Error loading assets: {e}")
        return

    # Generate predictions for both QNH and RH
    predictions = model.predict(X_test)
    
    # ---------------------------------------------------------
    # 1. Terminal Comparison Table (Both QNH & RH)
    # ---------------------------------------------------------
    print("\n" + "="*110)
    print(f"{'No':<4} | {'Actual QNH':<10} | {'AI QNH':<10} | {'Q Error':<8} | {'Actual RH':<10} | {'AI RH':<10} | {'R Error':<8}")
    print("-" * 110)
    
    for i in range(15): # Displaying first 15 samples
        act_q, pred_q = y_test.iloc[i, 0], predictions[i, 0]
        act_r, pred_r = y_test.iloc[i, 1], predictions[i, 1]
        
        q_error = abs(act_q - pred_q)
        r_error = abs(act_r - pred_r)
        
        print(f"{i+1:<4} | {act_q:<10.2f} | {pred_q:<10.2f} | {q_error:<8.2f} | {act_r:<10.1f} | {pred_r:<10.1f} | {r_error:<8.1f}")
    
    print("="*110)

    # ---------------------------------------------------------
    # 2. Visual Comparison Plots (Dual Axis/Subplots)
    # ---------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot for QNH Verification
    ax1.plot(y_test.iloc[:100, 0].values, label='Actual QNH', color='black', linewidth=1.5)
    ax1.plot(predictions[:100, 0], label='AI Prediction', color='red', linestyle='--', alpha=0.8)
    ax1.set_title('Aviation Weather Verification: QNH (hPa)')
    ax1.set_ylabel('Pressure (hPa)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot for RH Verification
    ax2.plot(y_test.iloc[:100, 1].values, label='Actual RH', color='blue', linewidth=1.5)
    ax2.plot(predictions[:100, 1], label='AI Prediction', color='green', linestyle='--', alpha=0.8)
    ax2.set_title('Aviation Weather Verification: Relative Humidity (%)')
    ax2.set_ylabel('Humidity (%)')
    ax2.set_xlabel('Time Samples')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    
    # Save the chart as an image
    save_path = os.path.join(SCRIPT_DIR, 'qnh_rh_verification_plot.png')
    plt.savefig(save_path)
    
    print(f"\nVerification graph saved to: {save_path}")
    plt.show()

if __name__ == "__main__":
    run_verification()