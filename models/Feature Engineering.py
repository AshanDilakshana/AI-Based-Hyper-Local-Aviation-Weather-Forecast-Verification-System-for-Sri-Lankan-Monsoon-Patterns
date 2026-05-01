import pandas as pd
import numpy as np

# 1. Load the cleaned data from the previous preprocessing step[cite: 1]
df = pd.read_csv('data/cleaned_data.csv')

# --- Convert temperature columns to numeric to avoid calculation errors ---
df['Dry tem(0C)'] = pd.to_numeric(df['Dry tem(0C)'], errors='coerce')
df['Dew point(0C)'] = pd.to_numeric(df['Dew point(0C)'], errors='coerce')

# 2. Clouds Encoding: Map cloud types to numeric values[cite: 1]
cloud_map = {'SKC': 0, 'NSC': 0, 'FEW': 1, 'SCT': 2, 'BKN': 3, 'OVC': 4}
df['Cloud_Level'] = df['Clouds'].str[:3].map(cloud_map).fillna(0)

# 3. Calculate Dew Point Depression (Important for fog/cloud prediction)[cite: 1]
df['Dew_Point_Depression'] = df['Dry tem(0C)'] - df['Dew point(0C)']

# 4. Create the Target Variable: Visibility Alert (1 if <5000m, else 0)[cite: 1]
df['Visibility_Status'] = np.where(df['Visibility'] < 5000, 1, 0)

# 5. Save the final features with the new standard name[cite: 1]
# Removing rows where calculation was not possible due to missing data
df.dropna(subset=['Dew_Point_Depression'], inplace=True)
df.to_csv('data/aviation_weather_features.csv', index=False)

print("Feature Engineering complete! aviation_weather_features.csv created.")