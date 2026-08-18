import os
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

def run_pipeline():
    print("🚀 Pipeline started...")

    print("🔄 Preprocessing...")
    preprocess_script = os.path.join(PROJECT_DIR, "preprocessing_and_feature_engineering", "preprocess_data.py")
    os.system(f"python \"{preprocess_script}\"")

    print("🔄 Feature Engineering...")
    feature_script = os.path.join(PROJECT_DIR, "preprocessing_and_feature_engineering", "feature_engineering.py")
    os.system(f"python \"{feature_script}\"")

    print("🔄 Training model (via MLOps Plugin)...")
    train_script = os.path.join(BASE_DIR, "mlops_retrainer_plugin.py")
    os.system(f"python \"{train_script}\"")

    print("✅ Pipeline completed at:", datetime.datetime.now())


if __name__ == "__main__":
    run_pipeline()