import pandas as pd
from backend.ml_pipeline.pipeline import WeatherDataPipeline
import warnings
warnings.filterwarnings('ignore')

def main():
    print("1. Loading raw dataset 'BIA_METAR_DATA_(2019_2024).xlsx'...")
    try:
        df = pd.read_excel('BIA_METAR_DATA_(2019_2024).xlsx')
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    print("2. Initializing Data Pipeline...")
    pipeline = WeatherDataPipeline()

    print("3. Running Preprocessing & Feature Engineering...")
    # This automatically cleans the data, creates features, and drops NAs
    X, y = pipeline.process_training_data(df)

    # Combine X (Features) and y (Target) so we can save it as one clean CSV
    processed_df = X.copy()
    processed_df['Target_Wind_Speed(Kts)'] = y

    # Save to the data folder
    save_path = 'backend/data/processed_monsoon_data.csv'
    processed_df.to_csv(save_path, index=False)

    print(f"\n✅ Success! The processed data has been saved to: {save_path}")
    print("\n--- Preview of the ready-to-train dataset ---")
    print(processed_df.head())
    print(f"\nTotal rows ready for training: {len(processed_df)}")

if __name__ == '__main__':
    main()
