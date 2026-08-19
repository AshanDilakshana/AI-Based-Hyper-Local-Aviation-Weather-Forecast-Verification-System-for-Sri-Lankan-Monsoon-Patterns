import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ActivityIcon, RadioTowerIcon, Loader2Icon } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { MetricCard } from '../components/ui/MetricCard';
import { ObservationTable } from '../components/ui/ObservationTable';
import { Panel } from '../components/ui/Panel';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { Sparkline } from '../components/ui/Sparkline';
import { ForecastMap } from '../components/dashboard/ForecastMap';
import type { Metric, Observation, Series, MetricTone } from '../types/weather';

const API_BASE = 'http://localhost:8000';

export function Dashboard() {
  const [range, setRange] = useState('06h - records');
  const { user } = useAuth();
  const navigate = useNavigate();

  const [currentMetrics, setCurrentMetrics] = useState<Metric[]>([]);
  const [recentObservations, setRecentObservations] = useState<Observation[]>([]);
  const [trendSeries, setTrendSeries] = useState<Series[]>([]);
  const [historicalSeries, setHistoricalSeries] = useState<Series[]>([]);
  const [lastUpdated, setLastUpdated] = useState<string>('--');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [currentRes, recentRes] = await Promise.all([
          axios.get(`${API_BASE}/live-metrology/current`),
          axios.get(`${API_BASE}/live-metrology/recent`)
        ]);

        const curr = currentRes.data;
        const recent = recentRes.data;

        // Map current data to MetricCards
        const metrics: Metric[] = [
          { label: 'Temperature', value: curr.dry_temp_c.toString(), unit: '°C', tone: 'amber' as MetricTone },
          { label: 'Dew Point', value: curr.dew_point_c.toString(), unit: '°C', tone: 'emerald' as MetricTone },
          { label: 'Humidity', value: curr.rh_percent.toString(), unit: '% RH', tone: 'cyan' as MetricTone },
          { label: 'Wind', value: curr.wind_speed_kts.toString(), unit: 'kt', footnote: `${curr.wind_dir}°`, tone: 'sky' as MetricTone },
          { label: 'Visibility', value: (curr.visibility >= 9999 ? '+10' : (curr.visibility / 1000).toString()), unit: 'km', tone: 'green' as MetricTone },
          { label: 'Pressure (QNH)', value: curr.qnh_hpa.toString(), unit: 'hPa', tone: 'slate' as MetricTone }
        ];
        setCurrentMetrics(metrics);

        // Formulate last updated string
        const formattedDate = new Date(curr.year, curr.month - 1, curr.date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
        const timeStr = curr.time_utc.padStart(4, '0');
        setLastUpdated(`${timeStr} UTC · ${formattedDate}`);

        // Map recent data to Observations table
        const obs: Observation[] = recent.map((r: any) => {
          const time = r.time_utc.padStart(4, '0');
          return {
            time: `${time.slice(0, 2)}:${time.slice(2, 4)} UTC`,
            temperature: `${r.dry_temp_c} °C`,
            pressure: `${r.qnh_hpa} hPa`,
            humidity: `${r.rh_percent}%`,
            windSpeed: `${r.wind_speed_kts} kt`,
            windDirection: `${r.wind_dir}°`,
            visibility: r.visibility >= 9999 ? '10+ km' : `${r.visibility / 1000} km`,
            cloudCoverage: r.clouds || 'N/A',
            rainfall: 'N/A' // Not present in metar data directly yet
          };
        });
        setRecentObservations(obs);

        // Map recent data to Sparklines
        // Reverse recent so it goes from oldest to newest
        const recentAsc = [...recent].reverse();
        const temps = recentAsc.map((r: any) => r.dry_temp_c);
        const pressures = recentAsc.map((r: any) => r.qnh_hpa);
        const humidities = recentAsc.map((r: any) => r.rh_percent);
        const winds = recentAsc.map((r: any) => r.wind_speed_kts);

        const currTemp = curr.dry_temp_c;
        const currPressure = curr.qnh_hpa;
        const currHumidity = curr.rh_percent;
        const currWind = curr.wind_speed_kts;

        const trends: Series[] = [
          { label: 'Temperature', value: `${currTemp}°C`, color: '#FBBF24', points: temps },
          { label: 'Wind Speed', value: `${currWind} kt`, color: '#22D3EE', points: winds },
          { label: 'Pressure', value: `${currPressure} hPa`, color: '#38BDF8', points: pressures }
        ];
        
        const historicals: Series[] = [
          { label: 'Temperature', value: `${currTemp}°C`, color: '#FBBF24', points: temps },
          { label: 'Pressure', value: `${currPressure} hPa`, color: '#38BDF8', points: pressures },
          { label: 'Humidity', value: `${currHumidity}% RH`, color: '#22D3EE', points: humidities }
        ];

        setTrendSeries(trends);
        setHistoricalSeries(historicals);

      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent-soft">
            Meteorological operations
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">METAR Dashboard</h1>
          <p className="mt-2 text-sm text-slate-400">
            BIA/CMB hyper-local weather intelligence · {lastUpdated}
          </p>
        </div>
        {user?.role === 'forecaster' ?
        <button
          type="button"
          onClick={() => navigate('/forecasting')}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-accent px-4 py-3 text-xs font-bold text-white transition-colors hover:bg-sky-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-soft">
          
            <ActivityIcon className="h-4 w-4" aria-hidden="true" />
            Generate Weather Forecast
          </button> :
        null}
      </header>

      {loading ? (
        <div className="flex h-64 items-center justify-center rounded-xl border border-line bg-panel">
          <Loader2Icon className="h-8 w-8 animate-spin text-accent-soft" />
        </div>
      ) : (
        <>
          <p className="text-sm text-slate-400">Last updated: {lastUpdated}</p>

          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
            {currentMetrics.map((metric) =>
            <MetricCard key={metric.label} {...metric} />
            )}
          </div>

          <Panel
            title="Recent MATAR weather observations"
            subtitle={`last refreshed ${lastUpdated}`}
            action={
            <SegmentedControl
              label="Observation window"
              options={['06h - records', '12h - records']}
              value={range}
              onChange={setRange} />
            }>
            
            <ObservationTable
              rows={recentObservations}
              timeLabel="Timestamp (UTC)"
              caption={`Recent METAR observations, ${range}`} />
            
          </Panel>

          <div className="grid gap-6 xl:grid-cols-3">
            <div className="xl:col-span-2">
              <ForecastMap />
            </div>
            <div className="xl:col-span-1 flex flex-col">
              <Panel title="trend monitor" subtitle="Recent History · Automatic station VCBI" className="h-full">
                <div className="flex flex-col gap-6">
                  {trendSeries.map((series) =>
                  <div key={series.label}>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-400">{series.label}</span>
                        <span className="text-xs font-semibold text-slate-100">{series.value}</span>
                      </div>
                      <div className="mt-2">
                        <Sparkline
                        points={series.points}
                        color={series.color}
                        ariaLabel={`${series.label} trend, currently ${series.value}`} />
                      </div>
                    </div>
                  )}
                </div>
              </Panel>
            </div>
          </div>

          <Panel
            title="Historical MATER observation trends"
            subtitle="API-derived station observations · recent history"
            action={
            <p className="flex items-center gap-2 text-xs text-slate-400">
                <RadioTowerIcon className="h-3.5 w-3.5" aria-hidden="true" />
                VCBI automatic weather station
              </p>
            }>
            
            <div className="grid gap-6 md:grid-cols-3">
              {historicalSeries.map((series) =>
              <div key={series.label}>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400">{series.label}</span>
                    <span className="text-xs font-semibold text-slate-100">{series.value}</span>
                  </div>
                  <div className="mt-3">
                    <Sparkline
                    points={series.points}
                    color={series.color}
                    height={80}
                    ariaLabel={`${series.label} history, currently ${series.value}`} />
                  
                  </div>
                </div>
              )}
            </div>
          </Panel>
        </>
      )}
    </div>
  );
}