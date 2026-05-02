import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

def train_aviation_model():
    # 1. දත්ත ගොනුව පූරණය කිරීම (Path එක නිවැරදි දැයි බලන්න)
    file_path = 'BIA_METAR_DATA_(2019_2024).xlsx'
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} සොයාගත නොහැක!")
        return

    print("Loading data and training model...")
    df = pd.read_excel(file_path)

    # 2. අවශ්‍ය columns තෝරා ගැනීම (ඔබේ dataset එකේ නම අනුව වෙනස් විය හැක)
    # මෙහිදී RH, Trend සහ Peak භාවිතා කර QNH අනාවැකි කීමට සූදානම් වේ
    X = df[['RH(%)', 'QNH_Trend', 'Humidity_Peak']] # Features
    y = df['QNH (hPa)']                             # Target

    # 3. මොඩලය නිර්මාණය කිරීම (Random Forest)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    # 4. 'models' නමින් ෆෝල්ඩරයක් නොමැති නම් එය නිර්මාණය කිරීම
    if not os.path.exists('models'):
        os.makedirs('models')

    # 5. මොඩලය .pkl ගොනුවක් ලෙස සුරැකීම
    model_filename = 'models/aviation_model.pkl'
    joblib.dump(model, model_filename)
    
    print(f"Success: Model saved at {model_filename}")

if __name__ == "__main__":
    train_aviation_model()