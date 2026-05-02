import "./Dashboard.css";
import { Link } from "react-router-dom";

export default function Dashboard() {
  return (
    <div className="dashboard">
      <div className="navbar">
        <h2>AeroMet AI</h2>

        <div className="nav-links">
          <Link to="/">Home</Link>
          <Link to="/" className="active">Dashboard</Link>
          <Link to="/forecast">Forecast</Link>
          <span>Verification</span>
          <span>Alerts</span>
          <span>Reports</span>
        </div>
      </div>

      <div className="container">
        <h2 className="title">Aviation Weather Dashboard</h2>

        <div className="grid">
          <div className="left">
            <div className="card">
              <h3>T+3 Forecast Parameters</h3>
              <div className="grid-3">
                <div className="box">Temp<br /><b>29°C</b></div>
                <div className="box">Humidity<br /><b>78%</b></div>
                <div className="box">Pressure<br /><b>1012 hPa</b></div>
                <div className="box">Wind Speed<br /><b>15 kt</b></div>
                <div className="box">Wind Dir<br /><b>240°</b></div>
                <div className="box">Visibility<br /><b>6 km</b></div>
              </div>
            </div>

            <div className="card">
              <h3>Verification: AI vs METAR vs TAF</h3>
              <table>
                <thead>
                  <tr>
                    <th>PARAMETER</th>
                    <th>AI</th>
                    <th>METAR</th>
                    <th>TAF</th>
                    <th>STATUS</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Temp</td>
                    <td>29.2</td>
                    <td>29</td>
                    <td>30</td>
                    <td className="ok">✔</td>
                  </tr>
                  <tr>
                    <td>Wind</td>
                    <td>15.5</td>
                    <td>14</td>
                    <td>10</td>
                    <td className="bad">✖</td>
                  </tr>
                  <tr>
                    <td>Visibility</td>
                    <td>6.2</td>
                    <td>6</td>
                    <td>8</td>
                    <td className="warn">⚠</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="card">
              <h3>Model Performance</h3>
              <div className="grid-3">
                <div className="box">MAE<br /><b>1.2</b></div>
                <div className="box">Consistency<br /><b>98.5%</b></div>
                <div className="box">Last Train<br /><b>24h ago</b></div>
              </div>
            </div>
          </div>

          <div className="right">
            <div className="card">
              <h3>Monsoon Context</h3>
              <p>Southwest Monsoon - Active</p>
              <p>Northeast Monsoon - Inactive</p>
            </div>

            <div className="card alert">
              <h3>Active Alerts</h3>
              <p className="red">⚠ Crosswind Risk</p>
              <p className="yellow">⚠ Low Visibility</p>
              <p className="blue">ℹ Pressure Drop</p>
            </div>

            <div className="card center">
              <h3>Forecast Reliability</h3>
              <div className="circle">87%</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}