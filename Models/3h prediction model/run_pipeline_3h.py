import pandas as pd
import sys
import os
import warnings

warnings.filterwarnings('ignore')

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, '../../')))

from pipeline_3h import WeatherDataPipeline3H

def main():
    print("1. Loading raw dataset 'BIA_METAR_DATA_(2019_2024).xlsx'...")
    raw_data_path = os.path.join(current_dir, '../../BIA_METAR_DATA_(2019_2024).xlsx')
    try:
        df = pd.read_excel(raw_data_path)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    print("2. Initializing 3H Data Pipeline...")
    pipeline = WeatherDataPipeline3H()

    print("3. Running Preprocessing & Feature Engineering (with 3H Shift)...")
    X, y = pipeline.process_training_data(df)

    processed_df = X.copy()
    processed_df['Target_Wind_Speed_3h_Ahead'] = y

    save_path = os.path.join(current_dir, '../../backend/data/processed_monsoon_data_3h.csv')
    processed_df.to_csv(save_path, index=False)

    print(f"\n✅ Success! The 3H processed data has been saved to: {save_path}")
    print(f"Total rows ready for 3H training: {len(processed_df)}")

if __name__ == '__main__':
    main()
