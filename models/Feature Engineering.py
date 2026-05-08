import pandas as pd
import numpy as np

# 1. Load the cleaned data from the previous preprocessing step
df = pd.read_csv('data/cleaned_data.csv')

# --- Convert Aviation-Critical columns to numeric ---
# Focus on parameters essential for takeoff performance
cols_to_fix = ['Dry tem(0C)', 'Dew point(0C)', 'RH(%)', 'QNH (hPa)', 'Visibility']
for col in cols_to_fix:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 2. Clouds Encoding: Map cloud types to numeric values
# This helps the AI understand cloud density (SKC=Clear, OVC=Overcast)
cloud_map = {'SKC': 0, 'NSC': 0, 'FEW': 1, 'SCT': 2, 'BKN': 3, 'OVC': 4}
df['Cloud_Level'] = df['Clouds'].str[:3].map(cloud_map).fillna(0)

# 3. Calculate Dew Point Depression (Aviation-Specific Feature)
# Crucial for predicting fog and low-cloud ceilings on the runway
df['Dew_Point_Depression'] = df['Dry tem(0C)'] - df['Dew point(0C)']

# 4. Target Variable Optimization
# Categorizing Visibility_Status for safety alerts (1 if <5000m, else 0)
df['Visibility_Status'] = np.where(df['Visibility'] < 5000, 1, 0)

# 5. Final Take-off Feature Selection
# Filtering only the columns required for the specialized Take-off Prediction Model
final_features = [
    'Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 
    'QNH (hPa)', 'Visibility', 'Cloud_Level', 'Visibility_Status'
]

# Removing rows where calculation was not possible due to missing takeoff data
df.dropna(subset=['Dew_Point_Depression', 'QNH (hPa)', 'RH(%)'], inplace=True)

# 6. Save the final features for model training
df[final_features].to_csv('data/aviation_weather_features.csv', index=False)

print("Feature Engineering complete! Specialized takeoff features saved to aviation_weather_features.csv")