import os
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_pipeline():
    print("🚀 Pipeline started...")

    print("🔄 Preprocessing...")
    os.system(f"python {BASE_DIR}/preprocess_data.py")

    print("🔄 Feature Engineering...")
    os.system(f"python {BASE_DIR}/feature_engineering.py")

    print("🔄 Training model...")
    os.system(f"python {BASE_DIR}/train_model.py")

    print("✅ Pipeline completed at:", datetime.datetime.now())


if __name__ == "__main__":
    run_pipeline()