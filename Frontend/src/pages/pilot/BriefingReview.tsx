import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { LiveFeedBadge, PageHeading } from '../../components/pilot/PageHeading';
import { StatCard } from '../../components/pilot/StatCard';
import { RouteDiagram } from '../../components/pilot/RouteDiagram';
import { MetricTile } from '../../components/pilot/MetricTile';
import { StatusPill } from '../../components/pilot/StatusPill';
import { DocumentsTable } from '../../components/pilot/DocumentsTable';
import { forecastStats } from '../../data/flight';
import { documents } from '../../data/documents';
import type { BriefingRow, WeatherMetric } from '../../types/aviation';

export function BriefingReview() {
  const [metrics, setMetrics] = useState<WeatherMetric[]>([]);
  const [briefing, setBriefing] = useState<BriefingRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchVerifiedData = async () => {
      try {
        const response = await axios.get('http://localhost:8000/forecasts/verified/latest');
        const data = response.data;
        
        // Map to metrics (excluding Headwind/Crosswind as requested)
        const mappedMetrics: WeatherMetric[] = [
          { label: 'Wind', value: `${data.wind_speed_kts ?? '-'} kt`, detail: 'Verified forecast', icon: 'wind' },
          { label: 'Visibility', value: `${((data.visibility ?? 0) / 1000).toFixed(1)} km`, detail: 'VMC conditions', icon: 'visibility' },
          { label: 'Temperature', value: `${data.dry_temp_c ?? '-'}°C`, detail: 'Verified forecast', icon: 'temperature' },
          { label: 'Cloud base', value: data.clouds || 'N/A', detail: 'Verified forecast', icon: 'cloud' },
        ];
        setMetrics(mappedMetrics);

        // Map to briefing rows
        const mappedBriefing: BriefingRow[] = [
          { label: 'Departure weather', value: `VMC · ${data.clouds || 'Clear'} clouds` },
          { label: 'En-route conditions', value: 'Light turbulence expected FL280–320' },
          { label: 'Destination weather', value: 'TEMPO SHRA after 18:00 UTC' },
          { label: 'Pressure / humidity', value: `${data.qnh_hpa ?? '-'} hPa · ${data.rh_percent ?? '-'}%` }
        ];
        setBriefing(mappedBriefing);
      } catch (err) {
        console.error('Error fetching verified forecast:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchVerifiedData();
  }, []);

  return (
    <div className="w-full space-y-6">
      <PageHeading
        eyebrow="Flight operations"
        title="Weather briefing"
        description="Verified aviation weather guidance for the active flight request."
        aside={<LiveFeedBadge />} />
      

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {forecastStats.map((stat) =>
        <StatCard key={stat.label} {...stat} />
        )}
      </div>

      <section className="rounded-xl border border-line bg-panel p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-sky-bright">
              Aviation weather briefing
            </p>
            <h2 className="mt-1 text-lg font-bold text-white">VCBI → WSSS corridor forecast</h2>
          </div>
          <StatusPill status="Approved" />
        </div>

        <div className="mt-5">
          <RouteDiagram
            origin={{ code: 'VCBI', city: 'Colombo' }}
            destination={{ code: 'WSSS', city: 'Singapore' }}
            caption="Indian Ocean route overview · FL350" />
          
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {loading ? (
            <p className="text-sm text-slate-400">Loading verified metrics...</p>
          ) : (
            metrics.map((metric) =>
              <MetricTile key={metric.label} {...metric} />
            )
          )}
        </div>
      </section>



      <section className="rounded-xl border border-line bg-panel p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white">My documents</h2>
            <p className="mt-1 text-xs text-subtle">
              Recent aviation weather briefings and flight history
            </p>
          </div>
          <Link
            to="/pilot/documents"
            className="text-sm font-semibold text-sky-bright transition-colors duration-150 ease-out hover:text-sky-soft">
            
            View all documents
          </Link>
        </div>
        <div className="mt-4">
          <DocumentsTable documents={documents.slice(0, 2)} />
        </div>
      </section>
    </div>);
}