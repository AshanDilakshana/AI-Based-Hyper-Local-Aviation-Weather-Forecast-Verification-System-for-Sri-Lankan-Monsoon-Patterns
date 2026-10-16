import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { ArrowDownIcon, ArrowRightIcon, RefreshCwIcon, CompassIcon, GaugeIcon } from 'lucide-react';
import { MetricCard } from '../components/ui/MetricCard';
import { ObservationTable } from '../components/ui/ObservationTable';
import { Panel } from '../components/ui/Panel';
import { VerificationForm } from '../components/forecast/VerificationForm';
import { Modal } from '../components/ui/Modal';
import { useTheme } from '../contexts/ThemeContext';

const API_BASE = 'http://localhost:8000';

// Format to DDHHMMZ (e.g., 121730Z)
const formatAviationTime = (dateNum: number, timeStr: string) => {
  if (!dateNum || !timeStr) return '--';
  const dd = dateNum.toString().padStart(2, '0');
  const hhmm = timeStr.split(':').slice(0, 2).join('');
  return `${dd}${hhmm}Z`;
};

// Format ISO date to DDHHMMZ
const formatIsoToAviationTime = (isoString: string) => {
  if (!isoString) return '--';
  const d = new Date(isoString);
  const dd = d.getUTCDate().toString().padStart(2, '0');
  const hh = d.getUTCHours().toString().padStart(2, '0');
  const mm = d.getUTCMinutes().toString().padStart(2, '0');
  return `${dd}${hh}${mm}Z`;
};


export function WeatherForecasting() {
  const [liveData, setLiveData] = useState<any>(null);
  const [recentData, setRecentData] = useState<any[]>([]);
  const [recentModels, setRecentModels] = useState<any[]>([]);
  const [forecastData, setForecastData] = useState<any>(null);
  const [lastVerified, setLastVerified] = useState<any>(null);

  const [refreshing, setRefreshing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string>('--');

  const [obsDuration, setObsDuration] = useState<6 | 12>(6);
  const [editData, setEditData] = useState<any>(null);
  const [isDensityModalOpen, setIsDensityModalOpen] = useState(false);

  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const bgImage = isDark ? '/aviation_runway_clouds.jpg' : '/aviation_runway_daylight.jpg';

  const fetchLiveData = async () => {
    try {
      const res = await axios.get(`${API_BASE}/live-metrology/current`);
      setLiveData(res.data);
      const timeStr = formatAviationTime(res.data.date, res.data.time_utc);
      setLastUpdated(timeStr);
    } catch (err) {
      console.error("Error fetching live data:", err);
    }
  };

  const fetchRecentData = async (duration: 6 | 12) => {
    try {
      // 30 min intervals => 2 per hour
      const limit = duration === 6 ? 12 : 24;
      const res = await axios.get(`${API_BASE}/live-metrology/recent?limit=${limit}`);
      setRecentData(res.data);
    } catch (err) {
      console.error("Error fetching recent data:", err);
    }
  };

  const fetchLastVerified = async () => {
    try {
      const res = await axios.get(`${API_BASE}/forecasts/verified/latest`);
      setLastVerified(res.data);
    } catch (err) {
      console.error("Error fetching verified forecast:", err);
    }
  };

  useEffect(() => {
    fetchLiveData();
    fetchLastVerified();
  }, []);

  const fetchRecentModels = async (duration: 6 | 12) => {
    try {
      const limit = duration === 6 ? 6 : 12;
      const res = await axios.get(`${API_BASE}/forecasts/recent-verified?limit=${limit}`);
      setRecentModels(res.data);
    } catch (err) {
      console.error("Error fetching recent verified forecasts:", err);
    }
  };

  useEffect(() => {
    fetchRecentData(obsDuration);
    fetchRecentModels(obsDuration);
  }, [obsDuration]);

  const runRefresh = async () => {
    setRefreshing(true);
    await fetchLiveData();
    await fetchRecentData(obsDuration);
    await fetchLastVerified();
    setRefreshing(false);
  };

  const runGenerate = async () => {
    if (!liveData) return;
    setGenerating(true);

    // We send an empty body if the backend doesn't strictly need it, 
    // or we can pass a payload if required by the new unified endpoint.
    // The unified endpoint `ai-predict-all` usually pulls the latest from DB,
    // but we can pass the payload just in case.
    const payload = {
      temperature: liveData.dry_temp_c || 28,
      dew_point: liveData.dew_point_c || 24,
      humidity: liveData.rh_percent || 80,
      wind_speed: liveData.wind_speed_kts || 10,
      wind_dir: liveData.wind_dir || 200,
      visibility: liveData.visibility || 9999,
      time_utc: liveData.time_utc,
      qnh_hpa: liveData.qnh_hpa || 1010
    };

    try {
      // The unified endpoint pulls the latest data directly from the DB,
      // so it is a GET request and does not need a payload body.
      const res = await axios.get(`${API_BASE}/forecasts/ai-predict-all`);
      setForecastData(res.data);
    } catch (err) {
      console.error("Error fetching forecast:", err);
    } finally {
      setGenerating(false);
    }
  };

  // Mapped Current Metrics
  const mappedCurrentMetrics = [
    { label: 'Temperature', value: liveData ? `${liveData.dry_temp_c}` : '--', unit: '°C', tone: 'amber' as const },
    { label: 'Pressure', value: liveData ? `${liveData.qnh_hpa}` : '--', unit: 'hPa', tone: 'sky' as const },
    { label: 'Visibility', value: liveData ? `${liveData.visibility}` : '--', unit: 'm', tone: 'green' as const },
    { label: 'Humidity', value: liveData ? `${liveData.rh_percent}` : '--', unit: '% RH', tone: 'cyan' as const },
    { label: 'Wind speed', value: liveData ? `${liveData.wind_speed_kts}` : '--', unit: 'kt', tone: 'emerald' as const },
    { label: 'Wind direction', value: liveData ? `${liveData.wind_dir}` : '--', unit: '°', tone: 'emerald' as const },
    { label: 'Cloud base', value: liveData?.clouds ? liveData.clouds.split(' ')[0] : '--', unit: '', tone: 'slate' as const },
    { label: 'Dew Point', value: liveData?.dew_point_c != null ? `${liveData.dew_point_c}` : '--', unit: '°C', tone: 'emerald' as const }
  ];

  // Mapped Forecast Metrics (For the Generate 3H section)
  const mappedForecastMetrics = [
    { label: 'Temperature', value: forecastData?.temperature_pressure_forecast?.prediction?.temperature_C !== undefined ? `${forecastData.temperature_pressure_forecast.prediction.temperature_C}` : '--', unit: '°C', tone: 'amber' as const },
    { label: 'Pressure', value: forecastData?.qnh_dewpoint_forecast?.predicted_qnh_3h !== undefined ? `${forecastData.qnh_dewpoint_forecast.predicted_qnh_3h}` : (forecastData?.temperature_pressure_forecast?.prediction?.pressure_hPa !== undefined ? `${forecastData.temperature_pressure_forecast.prediction.pressure_hPa}` : '--'), unit: 'hPa', tone: 'sky' as const },
    { label: 'Visibility', value: forecastData?.cloud_visibility_forecast?.visibility_prediction !== undefined ? `${forecastData.cloud_visibility_forecast.visibility_prediction}` : '--', unit: 'm', tone: 'green' as const },
    { label: 'Humidity', value: forecastData?.qnh_dewpoint_forecast?.derived_rh_3h !== undefined ? `${forecastData.qnh_dewpoint_forecast.derived_rh_3h}` : '--', unit: '% RH', tone: 'cyan' as const },
    { label: 'Wind speed', value: forecastData?.wind_forecast?.predicted_wind_speed_kts !== undefined ? `${forecastData.wind_forecast.predicted_wind_speed_kts}` : '--', unit: 'kt', tone: 'emerald' as const },
    { label: 'Wind direction', value: forecastData?.wind_forecast?.wind_dir !== undefined ? `${forecastData.wind_forecast.wind_dir}` : '--', unit: '°', tone: 'emerald' as const },
    { label: 'Cloud base', value: forecastData?.cloud_visibility_forecast?.cloud_status ? forecastData.cloud_visibility_forecast.cloud_status.replace('_', ' ') : '--', unit: '', tone: 'slate' as const },
    { label: 'Dew Point', value: forecastData?.qnh_dewpoint_forecast?.predicted_dewpoint_3h !== undefined && forecastData?.qnh_dewpoint_forecast?.predicted_dewpoint_3h !== null ? `${forecastData.qnh_dewpoint_forecast.predicted_dewpoint_3h}` : '--', unit: '°C', tone: 'emerald' as const }
  ];

  // Mapped Verified Metrics (For Last Forecast Details section)
  const verifiedMetrics = [
    { label: 'Temperature', value: lastVerified?.dry_temp_c ? `${lastVerified.dry_temp_c}` : '--', unit: '°C' },
    { label: 'Pressure', value: lastVerified?.qnh_hpa ? `${lastVerified.qnh_hpa}` : '--', unit: 'hPa' },
    { label: 'Wind speed', value: lastVerified?.wind_speed_kts ? `${lastVerified.wind_speed_kts}` : '--', unit: 'kt' },
    { label: 'Wind direction', value: lastVerified?.wind_dir ? `${lastVerified.wind_dir}` : '--', unit: '°' },
    { label: 'Humidity', value: lastVerified?.rh_percent ? `${lastVerified.rh_percent}` : '--', unit: '% RH' },
    { label: 'Cloud base', value: lastVerified?.clouds ? lastVerified.clouds : '--', unit: '' },
    { label: 'Visibility', value: lastVerified?.visibility ? `${lastVerified.visibility / 1000}` : '--', unit: 'km' }
  ];

  const mappedVerifiedDetails = [
    { label: 'Forecast ID', value: lastVerified ? `VF-${lastVerified.id}` : '--' },
    { label: 'Target Valid Time', value: lastVerified ? formatIsoToAviationTime(lastVerified.target_time) : '--' },
    { label: 'Verified At', value: lastVerified ? formatIsoToAviationTime(lastVerified.created_at) : '--' },
    { label: 'Status', value: lastVerified ? 'Verified & Active' : '--' },
  ];

  const mappedRecentObservations = recentData.map(obs => ({
    time: formatAviationTime(obs.date, obs.time_utc),
    temperature: `${obs.dry_temp_c} °C`,
    dewPoint: obs.dew_point_c != null ? `${obs.dew_point_c} °C` : '--',
    pressure: `${obs.qnh_hpa} hPa`,
    humidity: `${obs.rh_percent}%`,
    windSpeed: `${obs.wind_speed_kts} kt`,
    windDirection: `${obs.wind_dir}°`,
    visibility: `${obs.visibility} m`,
    cloudCoverage: `${obs.clouds || 'N/A'}`,
    rainfall: 'N/A'
  }));

  const mappedRecentModels = recentModels.map(model => ({
    time: formatIsoToAviationTime(model.target_time),
    temperature: model.dry_temp_c != null ? `${model.dry_temp_c} °C` : '--',
    dewPoint: model.dew_point_c != null ? `${model.dew_point_c} °C` : '--',
    pressure: model.qnh_hpa != null ? `${model.qnh_hpa} hPa` : '--',
    humidity: model.rh_percent != null ? `${model.rh_percent}%` : '--',
    windSpeed: model.wind_speed_kts != null ? `${model.wind_speed_kts} kt` : '--',
    windDirection: model.wind_dir != null ? `${model.wind_dir}°` : '--',
    visibility: model.visibility != null ? `${model.visibility} m` : '--',
    cloudCoverage: model.clouds || '--',
    rainfall: 'N/A'
  }));

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col gap-8"
    >
      {/* ── Hero / Current Observations Section ── */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="relative overflow-hidden rounded-3xl border border-line/60 bg-panel/85 backdrop-blur-xl p-6 sm:p-8 transition-all"
      >
        {/* Background Aviation Runway Clouds Image */}
        <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
          <img
            src={bgImage}
            alt="Aviation runway background"
            className="h-full w-full object-cover object-center transition-all duration-500"
          />
          {/* Shadow Overlay: Dark mode bg-black/80; Light mode bg-white/70 */}
          <div className={`absolute inset-0 transition-colors duration-500 ${isDark ? 'bg-black/80' : 'bg-white/70 backdrop-blur-[0.5px]'}`} />
        </div>
        {/* Decorative ambient background */}
        <div className="absolute top-0 right-0 h-[500px] w-[500px] -translate-y-1/2 translate-x-1/3 rounded-full bg-accent/5 blur-[90px] pointer-events-none animate-ambient-float" />
        <div className="absolute bottom-0 left-0 h-72 w-72 translate-y-1/3 -translate-x-1/3 rounded-full bg-sky-500/5 blur-[80px] pointer-events-none animate-ambient-float-delayed" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-start justify-between gap-6 mb-10">
          <div className="flex flex-col items-start max-w-2xl">
            <div className="inline-flex items-center gap-2.5 rounded-full bg-accent/10 px-4 py-1.5 mb-5 border border-accent/25 backdrop-blur-md shadow-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
              </span>
              <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent">VCBI Weather Intelligence</span>
            </div>

            <h1 className="text-3xl md:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-accent via-amber-300 to-amber-500 mb-3 tracking-tight">
              Weather Forecasting
            </h1>
            <p
              style={{ color: '#ffffff' }}
              className="text-white font-semibold text-sm md:text-base leading-relaxed drop-shadow-[0_2px_4px_rgba(0,0,0,0.9)]"
            >
              Live observation context and AI-supported aviation forecast guidance. Review real-time metrics and run predictive models.
            </p>
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="button"
            onClick={runRefresh}
            disabled={refreshing}
            className="group shrink-0 inline-flex items-center gap-3 rounded-2xl bg-panelDeep/90 backdrop-blur-md border border-line/80 px-6 py-3.5 text-sm font-semibold text-slate-200 shadow-lg transition-all hover:border-accent hover:shadow-accent/10 disabled:opacity-60 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <RefreshCwIcon className={`h-5 w-5 ${refreshing ? 'animate-spin text-accent' : 'text-slate-400 group-hover:text-accent transition-colors'}`} />
            <span className="flex flex-col items-start">
              <span className="text-[10px] uppercase tracking-wider text-slate-400 leading-none mb-1">{refreshing ? 'Syncing data...' : 'Last Updated'}</span>
              <span className="leading-none text-white font-bold tabular-nums">{lastUpdated}</span>
            </span>
          </motion.button>
        </div>

        <div className="relative z-10 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-5">
          {mappedCurrentMetrics.map((metric) =>
            <MetricCard key={metric.label} {...metric} />
          )}
        </div>
      </motion.section>

      {/* ── AI Forecast Engine Section ── */}
      <motion.section
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.65, delay: 0.15, ease: "easeOut" }}
        className="relative flex flex-col overflow-hidden rounded-3xl bg-panel/85 backdrop-blur-xl border border-line/70"
      >
        {/* Background Aviation Runway Clouds Image */}
        <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
          <img
            src={bgImage}
            alt="Aviation runway background"
            className="h-full w-full object-cover object-center transition-all duration-500"
          />
          {/* Shadow Overlay: Dark mode bg-black/40; Light mode bg-white/70 */}
          <div className={`absolute inset-0 transition-colors duration-500 ${isDark ? 'bg-black/40' : 'bg-white/70 backdrop-blur-[0.5px]'}`} />
        </div>
        <div className="absolute top-[-100px] right-[-100px] h-96 w-96 rounded-full bg-accent/10 blur-[100px] pointer-events-none" />

        <div className="relative z-10 flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between p-7 border-b border-line/50">
          <div>
            <h2
              style={{ color: '#ffffffff' }}
              className="text-2xl tracking-tight flex items-center gap-3 text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)]"
            >

              Hyper-local AI Forecast
            </h2>
            <p
              style={{ color: '#ffffff' }}
              className="!text-sm mt-2 font-medium flex items-center gap-2 text-white drop-shadow-[0_1px_3px_rgba(0,0,0,0.8)]"
            >
              <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]"></span> Target Horizon: +3 Hours Ahead
            </p>
          </div>

          <motion.button
            whileHover={{ scale: 1.03, boxShadow: "0 0 35px rgba(234,179,8,0.45)" }}
            whileTap={{ scale: 0.97 }}
            type="button"
            onClick={runGenerate}
            disabled={generating}
            className="group relative inline-flex items-center justify-center gap-2.5 rounded-2xl bg-gradient-to-r from-accent via-amber-400 to-amber-500 px-8 py-4 text-sm font-extrabold text-slate-900 shadow-[0_0_20px_rgba(234,179,8,0.3)] transition-all disabled:pointer-events-none disabled:opacity-70 focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
          >
            {generating ? 'Processing Models...' : 'Generate 3H Forecast'}
          </motion.button>
        </div>

        <div className="relative z-10 p-6 bg-slate-950/30">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-5">
            {mappedForecastMetrics.map((metric) =>
              <MetricCard key={metric.label} {...metric} />
            )}

            {/* HW / CW Headwind & Crosswind Card */}
            <motion.article
              whileHover={{ y: -3, transition: { duration: 0.2, ease: "easeOut" } }}
              className="col-span-1 sm:col-span-2 md:col-span-2 lg:col-span-2 min-w-0 flex flex-col justify-between rounded-2xl border border-line/60 bg-panel/80 backdrop-blur-md p-4 sm:p-5 shadow-sm transition-all duration-300 hover:border-sky-500/40 hover:shadow-xl hover:shadow-sky-500/5"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <CompassIcon className="h-4 w-4 text-sky-400" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Runway Wind Vector (HW / CW)</h3>
                </div>
                <span className="text-xs font-semibold text-accent-pale bg-accent/10 px-2.5 py-0.5 rounded-full border border-accent/20">
                  {forecastData?.wind_forecast?.runway ? forecastData.wind_forecast.runway : 'Runway: 04/22'}
                </span>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="flex flex-col">
                  <span className="flex items-center gap-1.5 text-xs font-medium text-slate-400 mb-1">
                    <ArrowDownIcon className="h-3.5 w-3.5 shrink-0 text-emerald-400" aria-hidden="true" />
                    Headwind:
                  </span>
                  <span className="text-xl sm:text-2xl font-black text-white tabular-nums">
                    {forecastData?.wind_forecast?.headwind_kts !== undefined ? Number(forecastData.wind_forecast.headwind_kts).toFixed(1) : '--'} <span className="text-xs font-semibold text-slate-400">kt</span>
                  </span>
                </div>
                <div className="flex flex-col">
                  <span className="flex items-center gap-1.5 text-xs font-medium text-slate-400 mb-1">
                    <ArrowRightIcon className="h-3.5 w-3.5 shrink-0 text-sky-400" aria-hidden="true" />
                    Crosswind:
                  </span>
                  <span className="text-xl sm:text-2xl font-black text-white tabular-nums">
                    {forecastData?.wind_forecast?.crosswind_kts !== undefined ? Number(forecastData.wind_forecast.crosswind_kts).toFixed(1) : '--'} <span className="text-xs font-semibold text-slate-400">kt</span>
                  </span>
                </div>
              </div>

              <div className="mt-3 pt-2.5 border-t border-line/40 flex items-center justify-between text-[11px] text-slate-400">
                <span>Calculated for active runway heading</span>
                <span className="text-emerald-400 font-semibold">ICAO Compliant</span>
              </div>
            </motion.article>

            {/* Density Altitude & VCBI Classification Card */}
            <motion.button
              whileHover={{ y: -3, scale: 1.005 }}
              whileTap={{ scale: 0.99 }}
              onClick={() => setIsDensityModalOpen(true)}
              className="col-span-1 sm:col-span-2 md:col-span-2 lg:col-span-2 rounded-2xl border border-accent/40 bg-gradient-to-r from-panel/90 via-panelDeep/95 to-panel/90 backdrop-blur-md p-4 sm:p-5 text-left transition-all hover:border-accent hover:shadow-[0_0_25px_-5px_rgba(234,179,8,0.35)] group flex flex-col justify-between gap-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent shadow-lg"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="h-7 w-7 rounded-xl bg-accent/15 border border-accent/30 flex items-center justify-center shrink-0">
                    <GaugeIcon className="h-4 w-4 text-accent" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-white group-hover:text-accent-pale transition-colors uppercase tracking-wider">
                      Density Altitude & Classification
                    </h3>
                  </div>
                </div>
                <ArrowRightIcon className="h-4 w-4 text-slate-500 group-hover:text-accent group-hover:translate-x-0.5 transition-all" />
              </div>

              <div className="mt-2 grid grid-cols-2 gap-4">
                <div className="flex flex-col">
                  <p className="flex items-baseline gap-1.5">
                    <span className="text-xl sm:text-2xl font-black tracking-tight text-white tabular-nums">
                      {forecastData?.temperature_pressure_forecast?.derived_parameters?.density_altitude_ft !== undefined ? Number(forecastData.temperature_pressure_forecast.derived_parameters.density_altitude_ft).toFixed(0) : '--'}
                    </span>
                    <span className="text-xs font-semibold text-slate-400">ft</span>
                  </p>
                  <p className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Density Altitude</p>
                </div>

                <div className="flex flex-col">
                  <p className="text-lg sm:text-xl font-black text-emerald-400 tracking-wide uppercase truncate">
                    {forecastData?.temperature_pressure_forecast?.derived_parameters?.classification ?? '--'}
                  </p>
                  <p className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Classification</p>
                </div>
              </div>

              <div className="mt-3 pt-2.5 border-t border-line/40 flex items-center justify-between text-[11px] text-slate-400">
                <span>Click for ISA deviation & performance</span>
                <span className="text-accent font-semibold">Details &rarr;</span>
              </div>
            </motion.button>
          </div>
        </div>
      </motion.section>

      <section className="flex flex-col gap-4">
        <h2 className="text-xl font-bold tracking-tight text-white" id="agent-verification-section">Agent verification</h2>
        <div className="rounded-xl border border-line bg-panel p-5 sm:p-6">
          <VerificationForm onSaveSuccess={() => { fetchLastVerified(); setEditData(null); }} editData={editData} prefillData={forecastData} />
        </div>
      </section>

      <Panel
        title="Last Forecast details"
        subtitle={lastVerified ? "Verified forecast data currently active on Pilot Dashboard" : "No verified forecasts available"}
        action={
          lastVerified ? (
            <button
              onClick={() => {
                setEditData(lastVerified);
                document.getElementById('agent-verification-section')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="text-xs font-semibold text-slate-400 hover:text-white px-2 py-1 rounded bg-ink border border-line transition-colors"
            >
              Edit
            </button>
          ) : undefined
        }>

        <div className="grid gap-8 lg:grid-cols-2">
          <dl className="flex flex-col gap-5">
            {mappedVerifiedDetails.map((detail) =>
              <div key={detail.label}>
                <dt className="text-[11px] tracking-wide text-slate-500">{detail.label}</dt>
                <dd className="mt-1 text-sm font-medium text-slate-200">{detail.value}</dd>
              </div>
            )}
          </dl>
          <div className="grid grid-cols-2 gap-x-6 gap-y-6 sm:grid-cols-3">
            {verifiedMetrics.map((metric) =>
              <div key={metric.label}>
                <p className="text-[13px] text-slate-300">{metric.label}</p>
                <p className="mt-1 flex items-baseline gap-1.5">
                  <span className="text-2xl font-bold leading-8 text-white">{metric.value}</span>
                  {metric.unit ? <span className="text-xs text-slate-500">{metric.unit}</span> : null}
                </p>
              </div>
            )}
          </div>
        </div>
      </Panel>

      <Panel
        title="Recent forecast outputs"
        subtitle={`Historical predicted values from the AI model`}
      >
        <div className="max-h-[400px] overflow-y-auto">
          <ObservationTable
            rows={mappedRecentModels}
            timeLabel="Target Time"
            caption="Recent forecast outputs" />
        </div>
      </Panel>

      <Panel
        title="Recent weather observations"
        subtitle={`Live observation feed for verification · last updated ${lastUpdated}`}
        action={
          <div className="flex bg-ink rounded-lg p-1 border border-line">
            <button
              onClick={() => setObsDuration(6)}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${obsDuration === 6 ? 'bg-accent text-white' : 'text-slate-400 hover:text-white'}`}
            >
              6H
            </button>
            <button
              onClick={() => setObsDuration(12)}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${obsDuration === 12 ? 'bg-accent text-white' : 'text-slate-400 hover:text-white'}`}
            >
              12H
            </button>
          </div>
        }>

        <div className="max-h-[400px] overflow-y-auto">
          <ObservationTable
            rows={mappedRecentObservations}
            timeLabel="Time"
            caption="Recent observation output" />
        </div>

      </Panel>

      <Modal
        isOpen={isDensityModalOpen}
        onClose={() => setIsDensityModalOpen(false)}
        title="Density Altitude Details"
      >
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg bg-ink border border-line p-3">
              <p className="text-xs text-slate-400 mb-1">Density Altitude</p>
              <p className="text-lg font-bold text-white">
                {forecastData?.temperature_pressure_forecast?.derived_parameters?.density_altitude_ft !== undefined ? Number(forecastData.temperature_pressure_forecast.derived_parameters.density_altitude_ft).toFixed(0) : '--'} ft
              </p>
            </div>
            <div className="rounded-lg bg-ink border border-line p-3">
              <p className="text-xs text-slate-400 mb-1">VCBI Classification</p>
              <p className="text-lg font-bold text-emerald-400 uppercase">
                {forecastData?.temperature_pressure_forecast?.derived_parameters?.classification ?? '--'}
              </p>
            </div>
            <div className="rounded-lg bg-ink border border-line p-3">
              <p className="text-xs text-slate-400 mb-1">Pressure Altitude</p>
              <p className="text-lg font-bold text-white">
                {forecastData?.temperature_pressure_forecast?.derived_parameters?.pressure_altitude_ft !== undefined ? Number(forecastData.temperature_pressure_forecast.derived_parameters.pressure_altitude_ft).toFixed(0) : '--'} ft
              </p>
            </div>
            <div className="rounded-lg bg-ink border border-line p-3">
              <p className="text-xs text-slate-400 mb-1">ISA Temperature</p>
              <p className="text-lg font-bold text-white">
                {forecastData?.temperature_pressure_forecast?.derived_parameters?.isa_temperature_c !== undefined ? Number(forecastData.temperature_pressure_forecast.derived_parameters.isa_temperature_c).toFixed(1) : '--'} °C
              </p>
            </div>
            <div className="rounded-lg bg-ink border border-line p-3">
              <p className="text-xs text-slate-400 mb-1">Temperature</p>
              <p className="text-lg font-bold text-white">
                {forecastData?.temperature_pressure_forecast?.prediction?.temperature_C !== undefined ? Number(forecastData.temperature_pressure_forecast.prediction.temperature_C).toFixed(1) : '--'} °C
              </p>
            </div>
            <div className="rounded-lg bg-ink border border-line p-3">
              <p className="text-xs text-slate-400 mb-1">Pressure (QNH)</p>
              <p className="text-lg font-bold text-white">
                {forecastData?.temperature_pressure_forecast?.prediction?.pressure_hPa !== undefined ? Number(forecastData.temperature_pressure_forecast.prediction.pressure_hPa).toFixed(1) : '--'} hPa
              </p>
            </div>
          </div>
          {forecastData?.temperature_pressure_forecast?.derived_parameters?.performance_impact && (
            <div className="rounded-lg bg-ink/50 border border-line p-3 mt-2">
              <p className="text-xs text-slate-400 mb-1">Performance Impact</p>
              <p className="text-sm text-slate-300">
                {forecastData.temperature_pressure_forecast.derived_parameters.performance_impact}
              </p>
            </div>
          )}
        </div>
      </Modal>
    </motion.div >
  );
}