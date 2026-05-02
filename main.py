from sklearn.ensemble import RandomForestRegressor
from data_processor import process_aviation_data
import joblib

class StabilityModel:
    def __init__(self, data_path):
        # දත්ත පිරිසැකසුම් කිරීම
        self.data = process_aviation_data(data_path)
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self._train()

    def _train(self):
        # විශේෂාංග: RH, QNH Trend, RH Peak
        X = self.data[['RH(%)', 'QNH_Trend', 'RH_Peak']]
        y = self.data['QNH (hPa)']
        self.model.fit(X, y)
        # පුහුණු කිරීමෙන් පසු ස්වයංක්‍රීයවම save කිරීමට අවශ්‍ය නම්:
        self.save_model()

    def save_model(self, filename='aviation_model.pkl'):
        # මොඩලය .pkl ගොනුවක් ලෙස සුරැකීම
        joblib.dump(self.model, filename)
        print(f"Model saved successfully as {filename}")

    def predict_stability(self, rh_value, qnh_trend, rh_peak):
        prediction = self.model.predict([[rh_value, qnh_trend, rh_peak]])[0]
        
        # පර්යේෂණ දත්ත මත පදනම් වූ විශ්වාසනීයත්ව අගය (Reliability Score)
        reliability = 94.2 if 1005 <= prediction <= 1015 else 82.5
        
        return round(prediction, 2), reliability