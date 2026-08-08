import pandas as pd
import numpy as np
import warnings
from sklearn.feature_selection import mutual_info_regression

warnings.filterwarnings('ignore')

print("Loading data...")
file_path = 'BIA_METAR_DATA_(2019_2024).xlsx'
df = pd.read_excel(file_path)

col_mapping = {
    'Wind Dir.': 'Wind Dir',
    'Dry tem(0C)': 'Dry Temp(0C)',
    'Dew point(0C)': 'Dew point(0C)', 
    'RH(%)': 'RH(%)',
    'QNH (hPa)': 'QNH(hPa)'
}
df.rename(columns=col_mapping, inplace=True)
df_monsoon = df[df['Month'].isin([5, 6, 7, 8, 9])].copy()

# Fix types
req_cols = ['Wind Dir', 'Wind speed(Kts)', 'Dry Temp(0C)', 'Dew point(0C)', 'RH(%)', 'QNH(hPa)', 'Visibility']
df_monsoon['Wind Dir'] = pd.to_numeric(df_monsoon['Wind Dir'], errors='coerce')
df_monsoon['Visibility'] = pd.to_numeric(df_monsoon['Visibility'], errors='coerce') # Might have "9999" or "10KM"

for col in req_cols:
    if col in df_monsoon.columns and col != 'Wind Dir':
        df_monsoon[col] = pd.to_numeric(df_monsoon[col], errors='coerce')

df_monsoon.ffill(inplace=True)
df_monsoon.dropna(subset=['Wind speed(Kts)', 'Dry Temp(0C)', 'QNH(hPa)', 'Dew point(0C)', 'Visibility'], inplace=True)

# 1. Advanced Feature Engineering
# Dew Point Depression
df_monsoon['Dew_Point_Depression'] = df_monsoon['Dry Temp(0C)'] - df_monsoon['Dew point(0C)']

# Circular Wind Direction
df_monsoon['Wind Dir_Sin'] = np.sin(np.radians(df_monsoon['Wind Dir']))
df_monsoon['Wind Dir_Cos'] = np.cos(np.radians(df_monsoon['Wind Dir']))

# Parse Time to create Lags and Tendencies
if all(c in df_monsoon.columns for c in ['Year', 'Month', 'Date', 'Time(UTC)']):
    time_str = df_monsoon['Time(UTC)'].astype(str).str.zfill(4)
    df_monsoon['Datetime'] = pd.to_datetime(
        df_monsoon['Year'].astype(str) + '-' +
        df_monsoon['Month'].astype(str) + '-' +
        df_monsoon['Date'].astype(str) + ' ' +
        time_str.str[:2] + ':' + time_str.str[2:4],
        errors='coerce'
    )
    df_monsoon.dropna(subset=['Datetime'], inplace=True)
    df_monsoon.sort_values('Datetime', inplace=True)
    df_monsoon.set_index('Datetime', inplace=True)
    
    # 3-Hour Lag
    df_shifted = df_monsoon[['QNH(hPa)', 'Dry Temp(0C)', 'Wind speed(Kts)']].copy()
    df_shifted.index = df_shifted.index + pd.Timedelta(hours=3)
    df_shifted.columns = [f"{col}_lag_3h" for col in df_shifted.columns]
    
    df_monsoon = df_monsoon.join(df_shifted, how='left')
    df_monsoon.dropna(subset=[f"{col}_lag_3h" for col in ['QNH(hPa)', 'Dry Temp(0C)', 'Wind speed(Kts)']], inplace=True)
    
    # Tendency Features
    df_monsoon['QNH_Tendency_3h'] = df_monsoon['QNH(hPa)'] - df_monsoon['QNH(hPa)_lag_3h']
    df_monsoon['Temp_Tendency_3h'] = df_monsoon['Dry Temp(0C)'] - df_monsoon['Dry Temp(0C)_lag_3h']
    
    df_monsoon.reset_index(inplace=True)

# Define all available numeric features for the analysis
features_to_test = [
    'Dry Temp(0C)', 'RH(%)', 'QNH(hPa)', 'Dew point(0C)', 'Visibility', 
    'Dew_Point_Depression', 'Wind Dir_Sin', 'Wind Dir_Cos',
    'QNH(hPa)_lag_3h', 'Dry Temp(0C)_lag_3h', 'Wind speed(Kts)_lag_3h',
    'QNH_Tendency_3h', 'Temp_Tendency_3h'
]

# Ensure they exist and no NAs
df_clean = df_monsoon[['Wind speed(Kts)'] + features_to_test].dropna()

# Correlation
print("\n--- Spearman Correlation with Wind Speed ---")
corrs = df_clean.corr(method='spearman')['Wind speed(Kts)'].sort_values(ascending=False)
print(corrs.drop('Wind speed(Kts)'))

# Mutual Information
print("\n--- Mutual Information Scores ---")
X = df_clean[features_to_test]
y = df_clean['Wind speed(Kts)']
mi_scores = mutual_info_regression(X, y, random_state=42)
mi_scores_series = pd.Series(mi_scores, index=features_to_test).sort_values(ascending=False)
print(mi_scores_series)

