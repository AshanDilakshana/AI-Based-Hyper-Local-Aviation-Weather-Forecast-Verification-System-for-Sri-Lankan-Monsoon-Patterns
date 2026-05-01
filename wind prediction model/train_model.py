import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os

def main():
    print("1. Loading processed data...")
    # Path to the processed dataset we generated earlier
    data_path = '../backend/data/processed_monsoon_data.csv'
    
    if not os.path.exists(data_path):
        print(f"Error: Could not find {data_path}. Please run the pipeline first.")
        return

    df = pd.read_csv(data_path)

    # Separate Features (X) and Target (y)
    target_col = 'Target_Wind_Speed(Kts)'
    X = df.drop(columns=[target_col])
    y = df[target_col]

    print("2. Splitting data into Training and Testing sets (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("3. Training XGBoost Regressor Model...")
    # Initialize the model with hyper-parameters suitable for weather data
    model = xgb.XGBRegressor(
        n_estimators=1000,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        objective='reg:squarederror',
        random_state=42
    )

    # Train the model
    model.fit(X_train, y_train)

    print("4. Evaluating Model Performance...")
    predictions = model.predict(X_test)
    
    import numpy as np
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))

    print("\n--- Model Accuracy ---")
    print(f"Mean Absolute Error (MAE): {mae:.2f} Knots")
    print(f"Root Mean Squared Error (RMSE): {rmse:.2f} Knots")
    print(f"(This means on average, the model's prediction is off by only {mae:.2f} knots)")

    print("\n5. Saving Trained Model...")
    # Save the model file inside this current folder
    model_save_path = 'xgboost_wind_model.json'
    model.save_model(model_save_path)
    print(f"✅ Model successfully saved to: {model_save_path}")

if __name__ == '__main__':
    main()
