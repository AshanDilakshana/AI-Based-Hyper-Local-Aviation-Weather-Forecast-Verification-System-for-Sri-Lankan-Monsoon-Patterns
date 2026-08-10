import { useState } from "react";
import axios from "axios";
import "./WeatherPrediction.css";
import { Link } from "react-router-dom";

export default function WeatherPrediction() {
  const [formData, setFormData] = useState({
    time_utc: "",
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

    try {
      const res = await axios.post("http://127.0.0.1:5000/predict", {
        time_utc: formData.time_utc,
        temperature: Number(formData.temperature),
        humidity: Number(formData.humidity),
        pressure: Number(formData.pressure),
        dew_point: Number(formData.dew_point),
        wind_speed: Number(formData.wind_speed),
        wind_direction: Number(formData.wind_direction),
        visibility: Number(formData.visibility),
      });

      setPrediction(res.data);
    } catch (error) {
      console.error(error);

      alert(
        error.response?.data?.error ||
        "Prediction failed. Check backend connection."
      );
    }
  };

  return (
    <div className="aviation-page">
      <div className="top-bar">
        <div>
          <h2>Aviation Weather Forecast Center</h2>
          <p>Bandaranaike International Airport (BIA)</p>
        </div>

        <div className="nav-links" style={{ display: "flex", gap: "20px", alignItems: "center", margin: "0 auto 0 40px" }}>
          <Link to="/" style={{ color: "#94a3b8", textDecoration: "none", fontWeight: "bold" }}>Dashboard</Link>
          <Link to="/forecast" style={{ color: "#60a5fa", textDecoration: "none", fontWeight: "bold", borderBottom: "2px solid #3b82f6" }}>Forecast Form</Link>
        </div>

        <span className="utc-badge">UTC System</span>
      </div>

      <div className="main-grid">

        {/* LEFT INPUT PANEL */}
        <form className="feed-card" onSubmit={handlePredict}>
          <h3>Live Weather Feed</h3>

          <label>Time (UTC)</label>
          <input
            type="text"
            name="time_utc"
            placeholder="0310"
            value={formData.time_utc}
            onChange={handleChange}
            required
          />

          <label>Dry Temperature (°C)</label>
          <input
            type="number"
            step="0.1"
            name="temperature"
            value={formData.temperature}
            onChange={handleChange}
            required
          />

          <label>Dew Point (°C)</label>
          <input
            type="number"
            step="0.1"
            name="dew_point"
            value={formData.dew_point}
            onChange={handleChange}
            required
          />

          <label>Relative Humidity (%)</label>
          <input
            type="number"
            name="humidity"
            value={formData.humidity}
            onChange={handleChange}
            required
          />

          <label>Wind Direction (°)</label>
          <input
            type="number"
            name="wind_direction"
            value={formData.wind_direction}
            onChange={handleChange}
            required
          />

          <label>Barometric Pressure QNH (hPa)</label>
          <input
            type="number"
            step="0.1"
            name="pressure"
            value={formData.pressure}
            onChange={handleChange}
            required
          />

          <label>Wind Speed (Kts)</label>
          <input
            type="number"
            step="0.1"
            name="wind_speed"
            value={formData.wind_speed}
            onChange={handleChange}
            required
          />

          <label>Visibility (m)</label>
          <input
            type="number"
            name="visibility"
            placeholder="9999"
            value={formData.visibility}
            onChange={handleChange}
            required
          />

          <button type="submit">
            Generate Forecast
          </button>
        </form>

        {/* RESULT AREA */}
        {!prediction ? (
          <div className="ready-card">
            <h2>System Ready</h2>

            <p>
              Enter live meteorological data to generate
              T+3 hour aviation weather forecast.
            </p>
          </div>
        ) : (
          <>
            {/* TEMPERATURE CARD */}
            <div className="result-card">
              <div className="result-header">
                <h3>Predicted Dry Temperature</h3>
                <span>SAFE</span>
              </div>

              <h1>{prediction.temperature.toFixed(2)}</h1>

              <p className="unit">°C</p>

              <div className="mini-box">
                <p>Forecast Type</p>
                <b>T+3 Hour</b>
              </div>

              <div className="mini-box">
                <p>Forecast UTC Time</p>
                <b>{prediction.forecast_time_utc}</b>
              </div>

              <p className="note">
                Temperature forecast generated using AI model.
              </p>
            </div>

            {/* PRESSURE CARD */}
            <div className="result-card">
              <div className="result-header">
                <h3>Predicted Pressure</h3>
                <span>SAFE</span>
              </div>

              <h1>{prediction.pressure.toFixed(2)}</h1>

              <p className="unit">hPa</p>

              <div className="mini-box">
                <p>Forecast Type</p>
                <b>T+3 Hour</b>
              </div>

              <div className="mini-box">
                <p>Forecast UTC Time</p>
                <b>{prediction.forecast_time_utc}</b>
              </div>

              <p className="note">
                Pressure forecast generated for next 3 hours.
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}