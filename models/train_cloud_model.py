import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import pickle

# 1. load data
df = pd.read_csv('data/aviation_weather_features.csv')
df.replace("No data", np.nan, inplace=True)

# clean data
cols = ['Dry tem(0C)', 'Dew_Point_Depression', 'RH(%)', 'QNH (hPa)']
for col in cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df.dropna(subset=cols + ['Cloud_Level'], inplace=True)

# 2. Features & Target
X = df[cols]
y = df['Cloud_Level']

# 3. Train-Test Split 
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 4. create Model 

model = RandomForestClassifier(
    n_estimators=500,        
    max_depth=20,            
    class_weight='balanced', 
    min_samples_split=2,
    random_state=42
)

model.fit(X_train, y_train)

# 5. check Accuracy
y_pred = model.predict(X_test)
print(f"Overall Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print("\nDetailed Performance for Each Category:")
print(classification_report(y_test, y_pred))

# 6. Save 
with open('models/cloud_prediction_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("\nSuccess: Model trained with equal attention to all weather conditions!")