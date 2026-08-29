import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
sys.path.append(PROJECT_ROOT)

from backend.mlops_retrainer.sync_training_data import sync_training_data
from Models.qnh_models.train_unified_3h import train_qnh_3h_model
from Models.dewpoint_models.train_unified_3h import train_dewpoint_3h_model


def run_qnh_dewpoint_retraining():
    """
    Automated MLOps Retraining for QNH and Dewpoint Models.
    This can be scheduled to run nightly or weekly.
    """
    print("Initiating Auto-Retraining for QNH and Dewpoint Models...")

    # 0. Sync JIT Data
    sync_training_data()

    try:
        print("Retraining QNH 3H Model...")
        # Assuming the train script saves the model automatically if successful
        train_qnh_3h_model()
        qnh_status = "Success"
    except Exception as e:
        qnh_status = f"Failed: {str(e)}"

    try:
        print("Retraining Dewpoint 3H Model...")
        train_dewpoint_3h_model()
        dewpoint_status = "Success"
    except Exception as e:
        dewpoint_status = f"Failed: {str(e)}"

    return {"QNH_3H_Model": qnh_status, "Dewpoint_3H_Model": dewpoint_status}


if __name__ == "__main__":
    results = run_qnh_dewpoint_retraining()
    print("\n--- Retraining Results ---")
    for model, status in results.items():
        print(f"{model}: {status}")
