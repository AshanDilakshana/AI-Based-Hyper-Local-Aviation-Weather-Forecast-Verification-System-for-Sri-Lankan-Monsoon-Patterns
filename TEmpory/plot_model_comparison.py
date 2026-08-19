import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../'))
DB_PATH = os.path.join(project_root, 'weather_data.db')

def generate_comparison_graph():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    
    # Load all prediction records (Ordered by newest first)
    predictions = pd.read_sql("SELECT * FROM prediction_records ORDER BY created_at DESC", engine)
    
    if predictions.empty:
        print("No predictions found in the database.")
        return
        
    # Load recent weather data for matching
    actuals = pd.read_sql("SELECT * FROM weather_data", engine)
    
    data = []
    
    for _, row in predictions.iterrows():
        try:
            target_year = int(row['target_year'])
            target_month = int(row['target_month'])
            target_date = int(row['target_date'])
            target_time = str(row['target_time_utc']).zfill(4)
            predicted_speed = float(row['predicted_wind_speed_kts'])
            forecast_type = row['forecast_type']
        except (ValueError, TypeError):
            continue
            
        match = actuals[
            (actuals['year'] == target_year) &
            (actuals['month'] == target_month) &
            (actuals['date'] == target_date) &
            (actuals['time_utc'] == target_time)
        ]
        
        if not match.empty:
            actual_speed = float(match.iloc[0]['wind_speed_kts'])
            error = abs(predicted_speed - actual_speed)
            
            # Create a datetime object for accurate sorting by target time
            target_dt_str = f"{target_year}-{target_month:02d}-{target_date:02d} {target_time[:2]}:{target_time[2:]}:00"
            
            data.append({
                'Forecast Type': forecast_type,
                'Error (Absolute)': error,
                'Target Datetime': pd.to_datetime(target_dt_str)
            })
            
    if not data:
        print("No verified predictions found to compare.")
        return
        
    df = pd.DataFrame(data)
    
    # Ensure data is sorted by Target Datetime descending (most recent targets first)
    df = df.sort_values(by='Target Datetime', ascending=False)
    
    # --- BALANCE SAMPLE SIZES ---
    counts = df['Forecast Type'].value_counts()
    min_count = counts.min()
    
    print("Sample sizes before balancing:")
    print(counts.to_string())
    print(f"\nBalancing all models to the minimum sample size: {min_count}\n")
    
    # Take the most recent `min_count` predictions for each model type
    df = df.groupby('Forecast Type').head(min_count).reset_index(drop=True)
    
    # Calculate Mean Absolute Error (MAE) per model
    mae_df = df.groupby('Forecast Type')['Error (Absolute)'].mean().reset_index()
    mae_df = mae_df.sort_values(by='Error (Absolute)')
    
    print("Mean Absolute Error (MAE) by Model (Lower is better, Balanced Sample Size):")
    print(mae_df.to_string(index=False))
    
    # Plotting
    plt.figure(figsize=(12, 6))
    sns.set_theme(style="whitegrid")
    
    # Box plot for distribution of errors
    plt.subplot(1, 2, 1)
    sns.boxplot(x='Forecast Type', y='Error (Absolute)', data=df, order=mae_df['Forecast Type'], hue='Forecast Type', legend=False)
    plt.title(f'Absolute Error Distribution (Sample Size = {min_count})')
    plt.xticks(rotation=45)
    
    # Bar plot for MAE
    plt.subplot(1, 2, 2)
    sns.barplot(x='Forecast Type', y='Error (Absolute)', data=mae_df, order=mae_df['Forecast Type'], hue='Forecast Type', palette="viridis", legend=False)
    plt.title(f'Mean Absolute Error (Sample Size = {min_count})')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plot_path = os.path.join(current_dir, 'model_comparison_plot.png')
    plt.savefig(plot_path)
    print(f"\nGraph successfully saved to: {plot_path}")
    
    # Open the image automatically on macOS
    os.system(f"open '{plot_path}'")

if __name__ == "__main__":
    generate_comparison_graph()
