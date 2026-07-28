import { useState, useEffect } from 'react';
import axios from 'axios';
import './index.css';
import LiveWeatherPanel from './components/LiveWeatherPanel';
import RecentDataPanel from './components/RecentDataPanel';
import ForecastingPanel from './components/ForecastingPanel';
import AircraftVisualizer from './components/AircraftVisualizer';
import { PlaneTakeoff } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [liveData, setLiveData] = useState(null);
  const [forecast, setForecast] = useState(null);

  const [recentData, setRecentData] = useState([]);

  // Fetch real live data
  const fetchLiveData = async () => {
    try {
      const res = await axios.get(`${API_BASE}/live-metrology/current`);
      setLiveData(res.data);
      
      const recentRes = await axios.get(`${API_BASE}/live-metrology/recent`);
      setRecentData(recentRes.data);
    } catch (err) {
      console.error("Error fetching live data", err);
    }
  };

  // Force an immediate external fetch from the backend
  const handleSyncNow = async () => {
    try {
      await axios.post(`${API_BASE}/live-metrology/sync`);
      await fetchLiveData();
    } catch (err) {
      console.error("Error forcing sync", err);
    }
  };

  useEffect(() => {
    fetchLiveData();
    // Auto-poll every 60 seconds (1 minute)
    const interval = setInterval(fetchLiveData, 60000);
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
          <LiveWeatherPanel data={liveData} onRefresh={handleSyncNow} />
          <RecentDataPanel recentData={recentData} />
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
              headwind={forecast.headwind_kts}
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
