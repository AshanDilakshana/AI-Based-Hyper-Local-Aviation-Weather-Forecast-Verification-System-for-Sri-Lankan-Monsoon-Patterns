import os
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def retrain_temperature_pressure_pipeline():
    """
    Executes the training script for the Temperature and Pressure models
    and returns a success boolean and a message.
    """
    try:
        train_script = os.path.join(BASE_DIR, "model", "random_forest", "train_quick_rf.py")
        
        print(f"🔄 Starting Temperature & Pressure Model Retraining...")
        
        # Run the training script as a subprocess
        result = subprocess.run(
            ["python", train_script], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            msg = "✅ Successfully retrained Temperature & Pressure Models. Metrics: " + result.stdout.split('--- SEPARATE RANDOM FOREST PERFORMANCE ---')[-1].strip()
            print(msg)
            return True, msg
        else:
            error_msg = f"❌ Error retraining Temperature/Pressure Models: {result.stderr}"
            print(error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = f"❌ Exception during Temperature/Pressure retraining: {str(e)}"
        print(error_msg)
        return False, error_msg

if __name__ == "__main__":
    success, message = retrain_temperature_pressure_pipeline()
    print(message)
