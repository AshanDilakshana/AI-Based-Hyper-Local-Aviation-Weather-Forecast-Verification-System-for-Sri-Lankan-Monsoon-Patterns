import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowDownIcon, ArrowRightIcon, RefreshCwIcon, SparklesIcon } from 'lucide-react';
import { MetricCard } from '../components/ui/MetricCard';
import { ObservationTable } from '../components/ui/ObservationTable';
import { Panel } from '../components/ui/Panel';
import { VerificationForm } from '../components/forecast/VerificationForm';

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
  const [forecastData, setForecastData] = useState<any>(null);
  const [lastVerified, setLastVerified] = useState<any>(null);

  const [refreshing, setRefreshing] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string>('--');
  
  const [obsDuration, setObsDuration] = useState<6 | 12>(6);
  const [editData, setEditData] = useState<any>(null);

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

  useEffect(() => {
    fetchRecentData(obsDuration);
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
    
    const payload = {
      temperature: liveData.dry_temp_c || 28,
      dew_point: liveData.dew_point_c || 24,
      humidity: liveData.rh_percent || 80,
      wind_dir: liveData.wind_dir || 200,
      runway_heading: 40,
      time_utc: liveData.time_utc,
      qnh_hpa: liveData.qnh_hpa
    };

    try {
      const res = await axios.post(`${API_BASE}/wind/predict/hybrid_3h`, payload);
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
    { label: 'Wind speed', value: liveData ? `${liveData.wind_speed_kts}` : '--', unit: 'kt', footnote: liveData ? `${liveData.wind_dir}°` : '', tone: 'emerald' as const },
    { label: 'Humidity', value: liveData ? `${liveData.rh_percent}` : '--', unit: '% RH', tone: 'cyan' as const },
    { label: 'Cloud base', value: liveData?.clouds ? liveData.clouds.split(' ')[0] : '--', unit: '', tone: 'slate' as const },
    { label: 'Visibility', value: liveData ? `${liveData.visibility}` : '--', unit: 'm', tone: 'green' as const },
    { label: 'Pressure', value: liveData ? `${liveData.qnh_hpa}` : '--', unit: 'hPa', tone: 'sky' as const }
  ];

  // Mapped Forecast Metrics (For the Generate 3H section)
  const mappedForecastMetrics = [
    { label: 'Temperature', value: '--', unit: '°C', tone: 'amber' as const },
    { label: 'Wind speed', value: forecastData ? `${forecastData.predicted_wind_speed_kts}` : '--', unit: 'kt', tone: 'emerald' as const },
    { label: 'Humidity', value: '--', unit: '% RH', tone: 'cyan' as const },
    { label: 'Cloud base', value: '--', unit: '', tone: 'slate' as const },
    { label: 'Visibility', value: '--', unit: 'm', tone: 'green' as const },
    { label: 'Pressure', value: '--', unit: 'hPa', tone: 'sky' as const }
  ];

  // Mapped Verified Metrics (For Last Forecast Details section)
  const verifiedMetrics = [
    { label: 'Temperature', value: lastVerified?.dry_temp_c ? `${lastVerified.dry_temp_c}` : '--', unit: '°C' },
    { label: 'Wind speed', value: lastVerified?.wind_speed_kts ? `${lastVerified.wind_speed_kts}` : '--', unit: 'kt', detail: lastVerified?.wind_dir ? `${lastVerified.wind_dir}°` : '' },
    { label: 'Humidity', value: lastVerified?.rh_percent ? `${lastVerified.rh_percent}` : '--', unit: '% RH' },
    { label: 'Cloud base', value: lastVerified?.clouds ? lastVerified.clouds : '--', unit: '' },
    { label: 'Visibility', value: lastVerified?.visibility ? `${lastVerified.visibility / 1000}` : '--', unit: 'km' },
    { label: 'Pressure', value: lastVerified?.qnh_hpa ? `${lastVerified.qnh_hpa}` : '--', unit: 'hPa' }
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
    pressure: `${obs.qnh_hpa} hPa`,
    humidity: `${obs.rh_percent}%`,
    windSpeed: `${obs.wind_speed_kts} kt`,
    windDirection: `${obs.wind_dir}°`,
    visibility: `${obs.visibility} m`,
    cloudCoverage: `${obs.clouds || 'N/A'}`,
    rainfall: 'N/A'
  }));

  return (
    <div className="flex flex-col gap-6">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent-soft">
          BIA/CMB weather intelligence
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">Weather Forecasting</h1>
        <p className="mt-2 text-sm text-slate-400">
          Live observation context and AI-supported aviation forecast guidance.
        </p>
        <button
          type="button"
          onClick={runRefresh}
          disabled={refreshing}
          className="mt-5 inline-flex items-center gap-2 rounded-lg border border-line-strong px-4 py-2.5 text-sm font-semibold text-slate-200 transition-colors hover:border-accent hover:text-white disabled:opacity-60 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent">
          
          <RefreshCwIcon className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} aria-hidden="true" />
          {refreshing ? 'Refreshing…' : 'Refresh data'}
        </button>
      </header>

      <p className="text-sm text-slate-400">Last updated: {lastUpdated}</p>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        {mappedCurrentMetrics.map((metric) =>
        <MetricCard key={metric.label} {...metric} />
        )}
      </div>

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-xl font-bold tracking-tight text-white">Hyper local model Forecasting</h2>
          <button
            type="button"
            onClick={runGenerate}
            disabled={generating}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-accent px-4 py-3 text-sm font-bold text-white transition-colors hover:bg-sky-400 disabled:opacity-70 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-soft">
            
            <SparklesIcon className="h-4 w-4" aria-hidden="true" />
            {generating ? 'Generating…' : 'Generate 3H Forecast'}
          </button>
        </div>
        <p className="text-sm text-slate-400">Target Time : {lastUpdated}</p>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-4 xl:grid-cols-8">
          {mappedForecastMetrics.slice(0, 2).map((metric) =>
          <MetricCard key={metric.label} {...metric} />
          )}
          <article className="rounded-xl border border-line bg-panel p-4">
            <h3 className="flex items-center gap-2 text-xs text-slate-400">
              <ArrowDownIcon className="h-4 w-4" aria-hidden="true" />
              Headwind
            </h3>
            <p className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-bold leading-8 text-white">{forecastData ? forecastData.headwind_kts : '--'}</span>
              <span className="text-xs text-slate-500">kt</span>
            </p>
            <p className="mt-3 text-[11px] text-slate-500">{forecastData?.runway ? forecastData.runway : 'Runway: --'}</p>
          </article>
          <article className="rounded-xl border border-line bg-panel p-4">
            <h3 className="flex items-center gap-2 text-xs text-slate-400">
              <ArrowRightIcon className="h-4 w-4" aria-hidden="true" />
              Crosswind
            </h3>
            <p className="mt-2 flex items-baseline gap-1.5">
              <span className="text-2xl font-bold leading-8 text-white">{forecastData ? forecastData.crosswind_kts : '--'}</span>
              <span className="text-xs text-slate-500">kt</span>
            </p>
          </article>
          {mappedForecastMetrics.slice(2).map((metric) =>
          <MetricCard key={metric.label} {...metric} />
          )}
        </div>
      </section>

      <section className="flex flex-col gap-4">
        <h2 className="text-xl font-bold tracking-tight text-white" id="agent-verification-section">Agent verification</h2>
        <div className="rounded-xl border border-line bg-panel p-5 sm:p-6">
          <VerificationForm onSaveSuccess={() => { fetchLastVerified(); setEditData(null); }} editData={editData} />
        </div>
      </section>

      <Panel
        title="Last Forecast details"
        subtitle={lastVerified ? "Verified forecast data currently active on Pilot Dashboard" : "No verified forecasts available"}
        action={
          <div className="flex gap-2">
            {lastVerified && (
              <button 
                onClick={() => {
                  setEditData(lastVerified);
                  document.getElementById('agent-verification-section')?.scrollIntoView({ behavior: 'smooth' });
                }}
                className="text-xs font-semibold text-slate-400 hover:text-white px-2 py-1 rounded bg-ink border border-line transition-colors"
              >
                Edit
              </button>
            )}
            <SparklesIcon className="h-5 w-5 text-emerald-400" aria-hidden="true" />
          </div>
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
                  {metric.detail ? <span className="text-xs text-slate-500 ml-1">{metric.detail}</span> : null}
                </p>
              </div>
            )}
          </div>
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
        
        <ObservationTable
          rows={mappedRecentObservations}
          timeLabel="Time"
          caption="Recent forecast output by target time" />
        
      </Panel>
    </div>);
}