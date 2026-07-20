import os
import sys
import pandas as pd

# Allow importing the common files from the parent 'Models' directory
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '../')))

from preprocessing_and_feature_engineering.wind_prediction_model.unified_pipeline import UnifiedWeatherPipeline
from wind_trainer import train_xgboost_model

def main():
    print("--- 1-Hour Unified Wind Forecasting Setup ---")
    
    # 1. Pipeline Execution
    raw_data_path = os.path.abspath(os.path.join(current_dir, '../../BIA_METAR_DATA_(2019_2024).xlsx'))
    processed_data_dir = os.path.abspath(os.path.join(current_dir, '../../backend/data'))
    os.makedirs(processed_data_dir, exist_ok=True)
    processed_data_path = os.path.join(processed_data_dir, 'processed_monsoon_data_1h.csv')

    print(f"Loading raw data from: {raw_data_path}")
    df = pd.read_excel(raw_data_path)

    print("Running Unified Pipeline for 1-Hour Forecast...")
    pipeline = UnifiedWeatherPipeline(forecast_hours=1)
    X, y = pipeline.process_training_data(df)

    processed_df = X.copy()
    processed_df[pipeline.target] = y
    processed_df.to_csv(processed_data_path, index=False)
    print(f"Processed 1H data saved to: {processed_data_path}")

    # 2. Model Training
    print("\nStarting Training Process...")
    train_xgboost_model(
        data_path=processed_data_path,
        target_col=pipeline.target,
        output_dir=current_dir,
        model_filename='xgboost_wind_model_unified.json'
    )

if __name__ == '__main__':
    main()
