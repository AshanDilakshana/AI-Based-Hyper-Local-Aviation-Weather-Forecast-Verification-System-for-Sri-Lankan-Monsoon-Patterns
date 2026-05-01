import pandas as pd

# 1. read data
file_path = 'data/BIA_METAR_DATA_(2019_2024).xlsx' 
df = pd.read_excel(file_path)

# 2. select First Inter-Monsoon (march/april)
df_sachi = df[df['Month'].isin([3, 4])].copy()

# 3. Visibility to numeric 
df_sachi['Visibility'] = pd.to_numeric(df_sachi['Visibility'], errors='coerce')

# 4. remove blanks
df_sachi.dropna(subset=['Visibility', 'Clouds'], inplace=True)

# save cleaned data
df_sachi.to_csv('data/cleaned_data.csv', index=False)
print("Preprocessing අවසන්! cleaned_data.csv folder created.")