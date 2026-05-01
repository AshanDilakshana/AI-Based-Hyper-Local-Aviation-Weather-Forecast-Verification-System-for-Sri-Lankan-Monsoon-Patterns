import os
import datetime

# Step 1: Preprocessing
print("🔄 Running preprocessing...")
os.system("python model/preprocess_data.py")

# Step 2: Feature Engineering
print("🔄 Running feature engineering...")
os.system("python model/feature_engineering.py")

# Step 3: Model Training
print("🔄 Training model...")
os.system("python model/train_model.py")

print("✅ Pipeline completed at:", datetime.datetime.now())