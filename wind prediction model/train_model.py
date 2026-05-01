import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
import os

def main():
    print("1. Loading processed data...")
    # Path to the processed dataset (Dynamic absolute path)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, '../backend/data/processed_monsoon_data.csv')
    
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

    print("3. Running Hyperparameter Tuning (GridSearchCV)...")
    print("   (Checking EVERY combination. This will take a few minutes...)")
    
    # We define a focused grid for Exhaustive Search
    # 3x3x2x2x2 = 72 combinations * 3 Folds = 216 total training runs!
    param_grid = {
        'n_estimators': [300, 500, 1000],
        'max_depth': [5, 7, 9],
        'learning_rate': [0.01, 0.05],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0]
    }

    base_model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)
    
    # GridSearchCV tests EVERY SINGLE combination in the param_grid
    search = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        scoring='neg_mean_absolute_error',
        cv=3,
        verbose=1,
        n_jobs=-1
    )

    search.fit(X_train, y_train)

    best_model = search.best_estimator_
    print(f"\n✅ Best Parameters Found: {search.best_params_}")

    print("\n4. Evaluating Model Performance...")
    
    # Predict on Training Data (To see how well it learned)
    train_predictions = best_model.predict(X_train)
    train_mae = mean_absolute_error(y_train, train_predictions)
    train_rmse = np.sqrt(mean_squared_error(y_train, train_predictions))
    train_r2 = r2_score(y_train, train_predictions)

    # Predict on Testing Data (To see how well it performs on unseen data)
    test_predictions = best_model.predict(X_test)
    test_mae = mean_absolute_error(y_test, test_predictions)
    test_rmse = np.sqrt(mean_squared_error(y_test, test_predictions))
    test_r2 = r2_score(y_test, test_predictions)

    print("\n" + "="*45)
    print("           MODEL ACCURACY REPORT           ")
    print("="*45)
    print("--- TRAINING SET (SEEN DATA) ---")
    print(f"Accuracy (R² Score):            {train_r2 * 100:.2f}%")
    print(f"Mean Absolute Error (MAE):      {train_mae:.2f} Knots")
    print(f"Root Mean Squared Error (RMSE): {train_rmse:.2f} Knots")
    
    print("\n--- TESTING SET (UNSEEN DATA) ---")
    print(f"Accuracy (R² Score):            {test_r2 * 100:.2f}%")
    print(f"Mean Absolute Error (MAE):      {test_mae:.2f} Knots")
    print(f"Root Mean Squared Error (RMSE): {test_rmse:.2f} Knots")
    print("="*45)

    # Check for overfitting (If train error is much lower than test error)
    if (test_mae - train_mae) > 0.5:
        print("\n⚠️ Note: The model might be slightly overfitting.")
        print("   (It memorized the training data instead of learning the patterns).")
    else:
        print("\n✅ Note: The model is well-balanced! No significant overfitting detected.")

    print("\n5. Saving Best Trained Model...")
    model_save_path = os.path.join(current_dir, 'xgboost_wind_model.json')
    best_model.save_model(model_save_path)
    print(f"✅ Model successfully saved to: {model_save_path}")

if __name__ == '__main__':
    main()
