import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
import random
import os

def main():
    print("1. Loading 3-Hour AI Model...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model = xgb.XGBRegressor()
    try:
        model.load_model(os.path.join(current_dir, 'xgboost_wind_model_3h.json'))
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    print("2. Loading 3-Hour Processed Data...")
    df = pd.read_csv(os.path.join(current_dir, '../backend/data/processed_monsoon_data_3h.csv'))
    
    target_col = 'Target_Wind_Speed_3h_Ahead'
    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Exactly the same random_state as training to ensure we only pick from the UNSEEN test set
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("3. Selecting 10 Random Unseen Records for Verification...\n")
    sample_indices = random.sample(range(len(X_test)), 10)
    X_samples = X_test.iloc[sample_indices]
    y_actual = y_test.iloc[sample_indices].values

    y_pred = model.predict(X_samples)

    print("="*75)
    print(f"{'3-HOUR FORECAST VERIFICATION (XGBoost)':^75}")
    print("="*75)
    print(f"{'Sample #':<10} | {'Real Future Speed (Kts)':<25} | {'AI Prediction (Kts)':<20} | {'Error (Kts)':<10}")
    print("-" * 75)
    
    for i in range(10):
        actual = y_actual[i]
        predicted = y_pred[i]
        diff = abs(actual - predicted)
        print(f"Test #{i+1:<4} | {actual:<25.2f} | {predicted:<20.2f} | {diff:.2f}")
    
    print("="*75)
    print("💡 Conclusion: Shows the actual vs predicted wind speeds for 3 hours into the future.")

if __name__ == "__main__":
    main()
