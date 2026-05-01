import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

# Load Excel dataset
df = pd.read_excel("data/BIA_METAR_DATA_(2019_2024).xlsx")

# Show column names
print("Columns in dataset:")
print(df.columns)

# Remove extra spaces from column names
df.columns = df.columns.str.strip()

# Show first 5 rows
print("\nFirst 5 rows:")
print(df.head())

# Remove unwanted empty column
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

# Convert required columns to numeric
df['Visibility'] = pd.to_numeric(df['Visibility'], errors='coerce')
df['RH(%)'] = pd.to_numeric(df['RH(%)'], errors='coerce')
df['Dry tem(0C)'] = pd.to_numeric(df['Dry tem(0C)'], errors='coerce')
df['Dew point(0C)'] = pd.to_numeric(df['Dew point(0C)'], errors='coerce')
df['QNH (hPa)'] = pd.to_numeric(df['QNH (hPa)'], errors='coerce')

# Drop rows only if important columns missing
df = df.dropna(subset=[
    'Visibility',
    'RH(%)',
    'Dry tem(0C)',
    'Dew point(0C)',
    'QNH (hPa)'
])

print("\nCleaned dataset shape:")
print(df.shape)

# Convert Time column to integer
df['Time(UTC)'] = df['Time(UTC)'].astype(int) 

# Create forecast blocks based on TAF periods 
df['forecast_block'] = pd.cut( df['Time(UTC)'], bins=[0, 600, 1200, 1800, 2400], labels=['Night', 'Morning', 'Afternoon', 'Evening'] )

 # Show forecast block distribution 
print("\nForecast Block Distribution:") 
print(df['forecast_block'].value_counts())

# Create fog risk label
df['fog_risk'] = ((df['Visibility'] < 5000) & (df['RH(%)'] > 85)).astype(int)

print("\nFog Risk Distribution:")
print(df['fog_risk'].value_counts())

# Select input features
X = pd.get_dummies(df[[
     'RH(%)', 
     'Dry tem(0C)', 
     'Dew point(0C)', 
     'QNH (hPa)', 
     'Visibility', 
     'forecast_block' 
     ]])

# Target variable 
y = df['fog_risk']
print("\nFeature matrix shape:", X.shape) 
print("Target shape:", y.shape)

# Split dataset
X_train, X_test, y_train, y_test = train_test_split( 
    X, y, 
    test_size=0.2, 
    random_state=42 
    )

print("\nTraining set shape:", X_train.shape)
print("Testing set shape:", X_test.shape)

# train model
model = RandomForestClassifier( 
    n_estimators=100,
      random_state=42
        )
model.fit(X_train, y_train)

print("\nModel Training Completed")

# Predictions
y_pred = model.predict(X_test)

# Accuracy 
accuracy = accuracy_score(y_test, y_pred)
print("\nModel Accuracy:", accuracy)

# Full report 
print("\nClassification Report:") 
print(classification_report(y_test, y_pred))

# Save trained model 
joblib.dump(model, "models/fog_model.pkl")
print("\nModel saved successfully")