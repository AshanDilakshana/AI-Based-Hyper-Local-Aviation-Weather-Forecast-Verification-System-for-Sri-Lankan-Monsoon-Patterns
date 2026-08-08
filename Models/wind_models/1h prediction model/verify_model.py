import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
import random
import os

def main():
    print("1. Loading AI Model...")
    model = xgb.XGBRegressor()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        model.load_model(os.path.join(current_dir, 'xgboost_wind_model.json'))
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    print("2. Loading Processed Data...")
    df = pd.read_csv(os.path.join(current_dir, '../../backend/data/processed_monsoon_data.csv'))
    
    target_col = 'Target_Wind_Speed(Kts)'
    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Re-create the exact same Test Set that the model did NOT see during training
    # By using the same random_state=42, we get the exact same 20% unseen data
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("3. Selecting 10 Random Unseen Records for Verification...\n")
    # Pick 10 random samples
    sample_indices = random.sample(range(len(X_test)), 10)
    X_samples = X_test.iloc[sample_indices]
    y_actual = y_test.iloc[sample_indices].values

    # Predict using the model
    y_pred = model.predict(X_samples)

    # Print the comparison table
    print("="*75)
    print(f"{'MODEL VERIFICATION: REAL DATA vs AI PREDICTION':^75}")
    print("="*75)
    print(f"{'Sample #':<10} | {'Real Wind Speed (Kts)':<25} | {'AI Prediction (Kts)':<20} | {'Error (Kts)':<10}")
    print("-" * 75)
    
    for i in range(10):
        actual = y_actual[i]
        predicted = y_pred[i]
        diff = abs(actual - predicted)
        
        # Formatting for clear viewing
        print(f"Test #{i+1:<4} | {actual:<25.2f} | {predicted:<20.2f} | {diff:.2f}")
    
    print("="*75)
    print("💡 Conclusion: The 'Error' column shows exactly how far off the AI is.")
    print("If the error is mostly between 0 and 2 Knots, the model is highly reliable.")

if __name__ == "__main__":
    main()
