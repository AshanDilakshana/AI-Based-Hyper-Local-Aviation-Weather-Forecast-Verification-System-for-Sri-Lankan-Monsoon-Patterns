import sys
import json
import joblib
import pandas as pd
from tensorflow.keras.models import load_model

lr_model = joblib.load("models/linear_regression_model.pkl")
rf_model = joblib.load("models/random_forest_model.pkl")
lstm_model = load_model("models/lstm_model.keras", compile=False)

temperature = float(sys.argv[1])
humidity = float(sys.argv[2])
pressure = float(sys.argv[3])

sample = pd.DataFrame([{
    "temperature": temperature,
    "humidity": humidity,
    "pressure": pressure
}])

lr_out = lr_model.predict(sample)
rf_out = rf_model.predict(sample)

sample_lstm = sample.values.reshape((1, 1, 3))
lstm_out = lstm_model.predict(sample_lstm)

final = (lr_out + rf_out + lstm_out) / 3

result = {
    "temperature_next_3h": round(float(final[0][0]), 2),
    "humidity_next_3h": round(float(final[0][1]), 2),
    "pressure_next_3h": round(float(final[0][2]), 2)
}

print(json.dumps(result))