import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
import os

def main():
    print("1. Loading processed 3H data...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, '../backend/data/processed_monsoon_data_3h.csv')
    
    if not os.path.exists(data_path):
        print(f"Error: Could not find {data_path}. Please run run_pipeline_3h.py first.")
        return

    df = pd.read_csv(data_path)

    target_col = 'Target_Wind_Speed_3h_Ahead'
    X = df.drop(columns=[target_col])
    y = df[target_col]

    print("2. Splitting data into Training and Testing sets (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("3. Running Massive Hyperparameter Tuning (RandomizedSearchCV)...")
    param_grid = {
        'n_estimators': [1000, 1500, 2000],
        'max_depth': [9, 11, 13, 15],
        'learning_rate': [0.005, 0.01, 0.02],
        'subsample': [0.7, 0.8, 0.9],
        'colsample_bytree': [0.7, 0.8, 0.9],
        'min_child_weight': [1, 3, 5],
        'gamma': [0, 0.1, 0.3]
    }

    base_model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42)
    
    # GridSearchCV tests EVERY SINGLE combination in the param_grid
    search = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=param_grid,
        n_iter=1000,
        scoring='neg_mean_absolute_error',
        cv=3,
        verbose=3, # Shows detailed progress for every fit
        n_jobs=-1,
        random_state=42
    )

    search.fit(X_train, y_train)
    best_model = search.best_estimator_
    print(f"\n✅ Best Parameters Found: {search.best_params_}")

    print("\n4. Evaluating 3H Model Performance...")
    
    train_predictions = best_model.predict(X_train)
    train_mae = mean_absolute_error(y_train, train_predictions)
    train_rmse = np.sqrt(mean_squared_error(y_train, train_predictions))
    train_r2 = r2_score(y_train, train_predictions)

    test_predictions = best_model.predict(X_test)
    test_mae = mean_absolute_error(y_test, test_predictions)
    test_rmse = np.sqrt(mean_squared_error(y_test, test_predictions))
    test_r2 = r2_score(y_test, test_predictions)

    print("\n" + "="*45)
    print("        3H MODEL ACCURACY REPORT           ")
    print("="*45)
    print("--- TRAINING SET ---")
    print(f"Accuracy (R² Score):            {train_r2 * 100:.2f}%")
    print(f"Mean Absolute Error (MAE):      {train_mae:.2f} Knots")
    
    print("\n--- TESTING SET (UNSEEN FUTURE DATA) ---")
    print(f"Accuracy (R² Score):            {test_r2 * 100:.2f}%")
    print(f"Mean Absolute Error (MAE):      {test_mae:.2f} Knots")
    print("="*45)

    print("\n5. Saving 3H Trained Model...")
    model_save_path = os.path.join(current_dir, 'xgboost_wind_model_3h.json')
    best_model.save_model(model_save_path)
    print(f"✅ Model successfully saved to: {model_save_path}")

if __name__ == '__main__':
    main()
