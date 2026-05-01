import { useState } from "react";
import axios from "axios";

export default function WeatherPrediction() {
  const [formData, setFormData] = useState({
    temperature: "",
    humidity: "",
    pressure: "",
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
    });

    setPrediction(res.data);
  };

  return (
    <div style={{ maxWidth: "600px", margin: "40px auto", fontFamily: "Arial" }}>
      <h2>AI Aviation Weather Prediction</h2>
      <p>T+3 Hour Forecast - Northeast Monsoon</p>

      <form onSubmit={handlePredict}>
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

        <button type="submit">Predict Next 3 Hours</button>
      </form>

      {prediction && (
        <div style={{ marginTop: "30px", padding: "20px", border: "1px solid #ccc" }}>
          <h3>Predicted Weather</h3>
          <p>Temperature: {prediction.temperature.toFixed(2)} °C</p>
          <p>Humidity: {prediction.humidity.toFixed(2)} %</p>
          <p>Pressure: {prediction.pressure.toFixed(2)} hPa</p>
        </div>
      )}
    </div>
  );
}