import os
import subprocess

def retrain() -> tuple[bool, str, str]:
    """
    Executes the training script for the Temperature and Pressure models
    and returns a tuple: (success_boolean, message, model_key).
    """
    try:
        # Assuming this file is in backend/mlops_plugins/
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        train_script = os.path.join(BASE_DIR, "Models", "Temperature", "train_quick_rf.py")
        
        print(f"Starting Temperature & Pressure Model Retraining via Plugin...")
        
        result = subprocess.run(
            ["python", train_script], 
            capture_output=True, 
            text=True
        )
        
        model_key = "Temperature_Pressure_Model"
        
        if result.returncode == 0:
            msg = "Successfully retrained Temperature & Pressure Models. Metrics: " + result.stdout.split('--- SEPARATE RANDOM FOREST PERFORMANCE ---')[-1].strip()
            print(msg)
            return True, msg, model_key
        else:
            error_msg = f"Error retraining Temperature/Pressure Models: {result.stderr}"
            print(error_msg)
            return False, error_msg, model_key
            
    except Exception as e:
        error_msg = f"Exception during Temperature/Pressure retraining: {str(e)}"
        print(error_msg)
        return False, error_msg, "Temperature_Pressure_Model"
