import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.feature_selection import mutual_info_regression
import warnings

warnings.filterwarnings('ignore')

def main():
    print("Loading data...")
    # Load dataset
    file_path = '../BIA_METAR_DATA_(2019_2024).xlsx'
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return

    # Ensure consistent column names
    col_mapping = {
        'Wind Dir.': 'Wind Dir',
        'Dry tem(0C)': 'Dry Temp(0C)',
        'Dew point(0C)': 'Dew point(0C)', 
        'RH(%)': 'RH(%)',
        'QNH (hPa)': 'QNH(hPa)'
    }
    df.rename(columns=col_mapping, inplace=True)

    # 1. Filter & Clean
    print("Filtering and cleaning data...")
    # Extract months 5, 6, 7, 8, 9
    df_monsoon = df[df['Month'].isin([5, 6, 7, 8, 9])].copy()

    # Drop missing values in crucial columns or coerce to numeric
    req_cols = ['Wind Dir', 'Wind speed(Kts)', 'Dry Temp(0C)', 'RH(%)', 'QNH(hPa)']
    
    # Wind Dir might have 'VRB' (variable), which we can treat as NaN for circular correlation
    df_monsoon['Wind Dir'] = pd.to_numeric(df_monsoon['Wind Dir'], errors='coerce')
    for col in req_cols:
        if col in df_monsoon.columns and col != 'Wind Dir':
            df_monsoon[col] = pd.to_numeric(df_monsoon[col], errors='coerce')
    
    # Handle missing values: forward fill then drop
    df_monsoon.ffill(inplace=True)
    df_monsoon.dropna(subset=req_cols, inplace=True)

    # Circular Encoding for Wind Dir
    df_monsoon['Wind Dir_Sin'] = np.sin(np.radians(df_monsoon['Wind Dir']))
    df_monsoon['Wind Dir_Cos'] = np.cos(np.radians(df_monsoon['Wind Dir']))
    
    # Advanced feature: Dew Point Depression (Dry Temp - Dew Point)
    if 'Dry Temp(0C)' in df_monsoon.columns and 'Dew point(0C)' in df_monsoon.columns:
        df_monsoon['Dew_Point_Depression'] = df_monsoon['Dry Temp(0C)'] - df_monsoon['Dew point(0C)']

    # 2. Feature Engineering: Create 3-hour lag features
    print("Creating 3-hour lag features...")
    if all(c in df_monsoon.columns for c in ['Year', 'Month', 'Date', 'Time(UTC)']):
        time_str = df_monsoon['Time(UTC)'].astype(str).str.zfill(4)
        df_monsoon['Hour'] = time_str.str[:2]
        df_monsoon['Minute'] = time_str.str[2:4]
        
        try:
            df_monsoon['Datetime'] = pd.to_datetime(
                df_monsoon['Year'].astype(str) + '-' +
                df_monsoon['Month'].astype(str) + '-' +
                df_monsoon['Date'].astype(str) + ' ' +
                df_monsoon['Hour'] + ':' +
                df_monsoon['Minute'],
                errors='coerce'
            )
            df_monsoon.dropna(subset=['Datetime'], inplace=True)
            df_monsoon.sort_values('Datetime', inplace=True)
            df_monsoon.set_index('Datetime', inplace=True)
            
            df_shifted = df_monsoon[['QNH(hPa)', 'Dry Temp(0C)', 'Wind speed(Kts)']].copy()
            df_shifted.index = df_shifted.index + pd.Timedelta(hours=3)
            df_shifted.columns = [f"{col}_lag_3h" for col in df_shifted.columns]
            
            df_monsoon = df_monsoon.join(df_shifted, how='left')
            df_monsoon.dropna(subset=[f"{col}_lag_3h" for col in ['QNH(hPa)', 'Dry Temp(0C)', 'Wind speed(Kts)']], inplace=True)
            df_monsoon.reset_index(inplace=True)
        except Exception as e:
            print(f"Warning: Datetime parsing failed, falling back to row-shift: {e}")
            df_monsoon['QNH(hPa)_lag_3h'] = df_monsoon['QNH(hPa)'].shift(6)
            df_monsoon['Dry Temp(0C)_lag_3h'] = df_monsoon['Dry Temp(0C)'].shift(6)
            df_monsoon['Wind speed(Kts)_lag_3h'] = df_monsoon['Wind speed(Kts)'].shift(6)
            df_monsoon.dropna(inplace=True)
    else:
        df_monsoon['QNH(hPa)_lag_3h'] = df_monsoon['QNH(hPa)'].shift(6)
        df_monsoon['Dry Temp(0C)_lag_3h'] = df_monsoon['Dry Temp(0C)'].shift(6)
        df_monsoon['Wind speed(Kts)_lag_3h'] = df_monsoon['Wind speed(Kts)'].shift(6)
        df_monsoon.dropna(inplace=True)

    # 3. Correlation Analysis
    print("Calculating Spearman Correlation...")
    numeric_cols = ['Wind speed(Kts)', 'Wind Dir_Sin', 'Wind Dir_Cos', 'QNH(hPa)', 'Dry Temp(0C)', 'RH(%)', 
                    'Dew_Point_Depression', 'QNH(hPa)_lag_3h', 'Dry Temp(0C)_lag_3h', 'Wind speed(Kts)_lag_3h']
    
    available_numeric = [col for col in numeric_cols if col in df_monsoon.columns]
    
    corr_matrix = df_monsoon[available_numeric].corr(method='spearman')
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", vmin=-1, vmax=1)
    plt.title('Spearman Correlation Heatmap (Monsoon Months)')
    plt.tight_layout()
    plt.savefig('spearman_correlation_heatmap.png')
    plt.close()
    print("Saved spearman_correlation_heatmap.png")

    # 4. Mutual Information Score
    print("Calculating Mutual Information Scores...")
    target = 'Wind speed(Kts)'
    features = ['QNH(hPa)', 'Dry Temp(0C)', 'RH(%)', 'Dew_Point_Depression', 'Wind Dir_Sin', 'Wind Dir_Cos', 'Wind speed(Kts)_lag_3h']
    
    # Only test features that successfully exist
    features_to_test = [f for f in features if f in df_monsoon.columns]
    
    if len(features_to_test) > 0 and target in df_monsoon.columns:
        # Drop NAs just for the MI calculation
        df_mi = df_monsoon[[target] + features_to_test].dropna()
        X = df_mi[features_to_test]
        y = df_mi[target]
        
        mi_scores = mutual_info_regression(X, y, random_state=42)
        mi_scores_series = pd.Series(mi_scores, index=features).sort_values(ascending=False)
        
        print("\n--- Mutual Information Scores (Target: Wind Speed) ---")
        print(mi_scores_series)
        print("-" * 52)
        
        plt.figure(figsize=(8, 5))
        mi_scores_series.plot(kind='bar', color='skyblue')
        plt.title('Mutual Information Scores with Wind Speed')
        plt.ylabel('MI Score')
        plt.tight_layout()
        plt.savefig('mutual_information_scores.png')
        plt.close()
        print("Saved mutual_information_scores.png")

    # 5. Visualization: Scatter plots with trend lines
    print("Generating visualizations...")
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    if 'QNH(hPa)' in df_monsoon.columns and 'Wind speed(Kts)' in df_monsoon.columns:
        sns.regplot(ax=axes[0], data=df_monsoon, x='QNH(hPa)', y='Wind speed(Kts)', 
                    scatter_kws={'alpha':0.3}, line_kws={'color':'red'}, order=2)
        axes[0].set_title('Pressure (QNH) vs Wind Speed (Monsoon)')
        axes[0].set_xlabel('QNH (hPa)')
        axes[0].set_ylabel('Wind Speed (Kts)')
    
    if 'Dry Temp(0C)' in df_monsoon.columns and 'Wind speed(Kts)' in df_monsoon.columns:
        sns.regplot(ax=axes[1], data=df_monsoon, x='Dry Temp(0C)', y='Wind speed(Kts)', 
                    scatter_kws={'alpha':0.3}, line_kws={'color':'red'}, order=2)
        axes[1].set_title('Temperature vs Wind Speed (Monsoon)')
        axes[1].set_xlabel('Dry Temp (0C)')
        axes[1].set_ylabel('Wind Speed (Kts)')
    
    plt.tight_layout()
    plt.savefig('scatter_plots_monsoon.png')
    plt.close()
    print("Saved scatter_plots_monsoon.png")
    
    print("Analysis complete. Check the generated PNG files for visualizations.")

if __name__ == "__main__":
    main()
