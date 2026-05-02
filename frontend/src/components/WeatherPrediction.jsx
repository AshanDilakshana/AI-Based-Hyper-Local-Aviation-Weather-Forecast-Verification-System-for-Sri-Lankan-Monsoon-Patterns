import { useState } from "react";
import axios from "axios";
import "./WeatherPrediction.css";

export default function WeatherPrediction() {
  const [formData, setFormData] = useState({
    temperature: "",
    humidity: "",
    pressure: "",
    dew_point: "",
    wind_speed: "",
    wind_direction: "",
    visibility: "",
  });

  const [prediction, setPrediction] = useState(null);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handlePredict = async (e) => {
    e.preventDefault();

    const res = await axios.post("http://127.0.0.1:5000/predict", {
      temperature: Number(formData.temperature),
      humidity: Number(formData.humidity),
      pressure: Number(formData.pressure),
      dew_point: Number(formData.dew_point),
      wind_speed: Number(formData.wind_speed),
      wind_direction: Number(formData.wind_direction),
      visibility: Number(formData.visibility),
    });

    setPrediction(res.data);
  };

  return (
    <div className="weather-page">
      <div className="weather-card">
        <div className="weather-header">
          <div>
            <h2>AI Aviation Weather Prediction</h2>
            <p>T+3 Hour Forecast - Northeast Monsoon</p>
          </div>

          <button className="verify-btn">T-1h Verification</button>
        </div>

        <form className="weather-form" onSubmit={handlePredict}>
          <input
            type="number"
            name="temperature"
            placeholder="Temperature (°C)"
            value={formData.temperature}
            onChange={handleChange}
            required
          />

          <input
            type="number"
            name="humidity"
            placeholder="Humidity (%)"
            value={formData.humidity}
            onChange={handleChange}
            required
          />

          <input
            type="number"
            name="pressure"
            placeholder="Pressure (hPa)"
            value={formData.pressure}
            onChange={handleChange}
            required
          />

          <input
            type="number"
            name="dew_point"
            placeholder="Dew Point (°C)"
            value={formData.dew_point}
            onChange={handleChange}
            required
          />

          <input
            type="number"
            name="wind_speed"
            placeholder="Wind Speed (Kts)"
            value={formData.wind_speed}
            onChange={handleChange}
            required
          />

          <input
            type="number"
            name="wind_direction"
            placeholder="Wind Direction (°)"
            value={formData.wind_direction}
            onChange={handleChange}
            required
          />

          <input
            type="number"
            name="visibility"
            placeholder="Visibility (km)"
            value={formData.visibility}
            onChange={handleChange}
            required
          />

          <button type="submit" className="predict-btn">
            Predict Next 3 Hours
          </button>
        </form>

        {prediction && (
          <div className="prediction-box">
            <h3>Predicted Weather</h3>

            <table>
              <thead>
                <tr>
                  <th>PARAMETER</th>
                  <th>AI MODEL</th>
                  <th>STATUS</th>
                </tr>
              </thead>

              <tbody>
                <tr>
                  <td>Temp (°C)</td>
                  <td className="ai-value">
                    {prediction.temperature.toFixed(2)}
                  </td>
                  <td className="success">✓</td>
                </tr>

                <tr>
                  <td>Humidity (%)</td>
                  <td className="ai-value">
                    {prediction.humidity.toFixed(2)}
                  </td>
                  <td className="success">✓</td>
                </tr>

                <tr>
                  <td>Press (hPa)</td>
                  <td className="ai-value">
                    {prediction.pressure.toFixed(2)}
                  </td>
                  <td className="success">✓</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}