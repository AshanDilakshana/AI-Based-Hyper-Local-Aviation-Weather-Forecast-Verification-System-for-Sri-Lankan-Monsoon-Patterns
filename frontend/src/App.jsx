import { useState, useEffect } from 'react';
import axios from 'axios';
import './index.css';
import LiveWeatherPanel from './components/LiveWeatherPanel';
import ForecastingPanel from './components/ForecastingPanel';
import AircraftVisualizer from './components/AircraftVisualizer';
import { PlaneTakeoff } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [liveData, setLiveData] = useState(null);
  const [forecast, setForecast] = useState(null);

  // Fetch live mock data
  const fetchLiveData = async () => {
    try {
      const res = await axios.get(`${API_BASE}/mock-metrology/current`);
      setLiveData(res.data);
    } catch (err) {
      console.error("Error fetching live data", err);
    }
  };

  useEffect(() => {
    fetchLiveData();
    // Auto-poll every 10 seconds
    const interval = setInterval(fetchLiveData, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <header className="header">
        <h1><PlaneTakeoff size={36} style={{ verticalAlign: 'middle', marginRight: '12px' }}/> Aviation Weather AI</h1>
        <p>Hyper-Local Wind Forecast System - BIA</p>
      </header>

      <main className="dashboard-container">
        <div className="left-column">
          <LiveWeatherPanel data={liveData} onRefresh={fetchLiveData} />
        </div>
        
        <div className="right-column">
          <ForecastingPanel 
            liveData={liveData} 
            apiBase={API_BASE} 
            onForecastComplete={(data) => setForecast(data)} 
          />
          {forecast && (
            <AircraftVisualizer 
              windDir={liveData?.wind_dir || 0} 
              crosswind={forecast.crosswind_kts}
              status={forecast.status}
              runwayHeading={40} // Default RWY 04
            />
          )}
        </div>
      </main>
    </>
  );
}

export default App;
