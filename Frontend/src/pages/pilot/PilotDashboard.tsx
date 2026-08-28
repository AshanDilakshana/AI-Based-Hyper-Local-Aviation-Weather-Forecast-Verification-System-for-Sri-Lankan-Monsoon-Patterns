import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { PlusIcon } from 'lucide-react';
import { LiveFeedBadge, PageHeading } from '../../components/pilot/PageHeading';
import { StatCard } from '../../components/pilot/StatCard';
import { RouteDiagram } from '../../components/pilot/RouteDiagram';
import { StatusPill } from '../../components/pilot/StatusPill';
import { flightStats, routeMapImage } from '../../data/flight';
import { useAuth } from '../../contexts/AuthContext';

const AIRPORT_DATA: Record<string, { city: string, country: string, lat: number, lon: number }> = {
  'VCBI': { city: 'Colombo', country: 'Sri Lanka', lat: 7.18, lon: 79.88 },
  'CMB': { city: 'Colombo', country: 'Sri Lanka', lat: 7.18, lon: 79.88 },
  'AUH': { city: 'Abu Dhabi', country: 'UAE', lat: 24.43, lon: 54.65 },
  'OMAA': { city: 'Abu Dhabi', country: 'UAE', lat: 24.43, lon: 54.65 },
  'WSSS': { city: 'Singapore', country: 'Singapore', lat: 1.36, lon: 103.99 },
  'SIN': { city: 'Singapore', country: 'Singapore', lat: 1.36, lon: 103.99 },
  'YMML': { city: 'Melbourne', country: 'Australia', lat: -37.67, lon: 144.84 },
  'MEL': { city: 'Melbourne', country: 'Australia', lat: -37.67, lon: 144.84 },
  'OMDB': { city: 'Dubai', country: 'UAE', lat: 25.25, lon: 55.36 },
  'DXB': { city: 'Dubai', country: 'UAE', lat: 25.25, lon: 55.36 },
  'OTHH': { city: 'Doha', country: 'Qatar', lat: 25.27, lon: 51.61 },
  'DOH': { city: 'Doha', country: 'Qatar', lat: 25.27, lon: 51.61 },
  'EGLL': { city: 'London', country: 'UK', lat: 51.47, lon: -0.45 },
  'LHR': { city: 'London', country: 'UK', lat: 51.47, lon: -0.45 },
  'WMKK': { city: 'Kuala Lumpur', country: 'Malaysia', lat: 2.74, lon: 101.70 },
  'KUL': { city: 'Kuala Lumpur', country: 'Malaysia', lat: 2.74, lon: 101.70 },
  'VRMM': { city: 'Male', country: 'Maldives', lat: 4.19, lon: 73.53 },
  'MLE': { city: 'Male', country: 'Maldives', lat: 4.19, lon: 73.53 },
  'VTBS': { city: 'Bangkok', country: 'Thailand', lat: 13.69, lon: 100.75 },
  'BKK': { city: 'Bangkok', country: 'Thailand', lat: 13.69, lon: 100.75 },
};

function getAirportInfo(code: string) {
  const upperCode = code?.toUpperCase().trim() || '';
  return AIRPORT_DATA[upperCode] || { city: upperCode || 'Unknown', country: '', lat: 7.18, lon: 79.88 };
}

export function PilotDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [lastPlan, setLastPlan] = useState<any>(null);

  useEffect(() => {
    if (user?.reference) {
      axios.get(`http://localhost:8000/pilot/last-flight-plan?pilot_reference=${user.reference}`)
        .then(res => {
          if (res.data && res.data.flight_no) {
            setLastPlan(res.data);
          }
        })
        .catch(err => console.error("Could not fetch last plan:", err));
    }
  }, [user]);

  let originInfo = { city: 'Departure', country: '', lat: 7.18, lon: 79.88 };
  let destInfo = { city: 'Destination', country: '', lat: 7.18, lon: 79.88 };
  let mapUrl = 'https://globe.adsbexchange.com/?lat=7.18&lon=79.88&zoom=6';

  if (lastPlan) {
    originInfo = getAirportInfo(lastPlan.departure);
    destInfo = getAirportInfo(lastPlan.destination);
    
    // Auto-center map on midpoint
    const midLat = (originInfo.lat + destInfo.lat) / 2;
    const midLon = (originInfo.lon + destInfo.lon) / 2;
    
    const latDiff = Math.abs(originInfo.lat - destInfo.lat);
    const lonDiff = Math.abs(originInfo.lon - destInfo.lon);
    const maxDiff = Math.max(latDiff, lonDiff);
    
    let zoom = 5;
    if (maxDiff > 60) zoom = 3;
    else if (maxDiff > 30) zoom = 4;
    else if (maxDiff > 10) zoom = 5;
    else zoom = 6;
    
    mapUrl = `https://embed.windy.com/embed2.html?lat=${midLat.toFixed(2)}&lon=${midLon.toFixed(2)}&zoom=${zoom}&level=500h&overlay=wind&menu=&message=&marker=&calendar=&pressure=&type=map&location=coordinates&detail=&detailLat=${destInfo.lat}&detailLon=${destInfo.lon}&metricWind=kt&metricTemp=%C2%B0C&radarRange=-1`;
  }

  return (
    <div className="w-full space-y-6">
      <PageHeading
        eyebrow="Flight operations"
        title={`Good morning, ${user?.name ?? 'Captain'}.`}
        description="Build a verified aviation weather briefing for your next flight."
        aside={<LiveFeedBadge />} />
      

      <section className="flex flex-col gap-4 rounded-xl border border-line bg-panel p-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-sky-bright">
            Next flight workflow
          </p>
          <h2 className="mt-1 text-lg font-bold text-white">Create a weather briefing request</h2>
          <p className="mt-1 text-sm text-subtle">
            Provide route, departure time, and destination details for ICAO-aligned meteorological
            review.
          </p>
        </div>
        <button
          type="button"
          onClick={() => navigate('/pilot/flight-planning')}
          className="inline-flex h-10 shrink-0 items-center gap-2 rounded-lg bg-accent px-4 text-sm font-semibold text-white transition-colors duration-150 ease-out hover:bg-sky-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-bright">
          
          <PlusIcon className="h-4 w-4" aria-hidden="true" />
          Flight planning
        </button>
      </section>

      <section aria-labelledby="recent-plan" className="space-y-4">
        <h2 id="recent-plan" className="text-lg font-bold text-white">
          Recent created flight plan details
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {lastPlan ? (
            <>
              <StatCard icon="route" label="Flight Route" value={`${lastPlan.departure} → ${lastPlan.destination}`} />
              <StatCard icon="aircraft" label="Flight Number" value={lastPlan.flight_no} />
              <StatCard icon="terminal" label="Departure Time" value={new Date(lastPlan.departure_time).toLocaleString()} />
              <StatCard icon="duration" label="Duration" value={`${Math.floor(lastPlan.duration_mins / 60)}h ${lastPlan.duration_mins % 60}m`} />
            </>
          ) : (
            <div className="col-span-full rounded-lg border border-line bg-ink p-8 text-center">
              <p className="text-sm text-subtle">No recent flight plans found. Create a new request above.</p>
            </div>
          )}
        </div>
      </section>

      {lastPlan && (
        <section className="rounded-xl border border-line bg-panel p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-sky-bright">
                Aviation weather briefing
              </p>
              <h2 className="mt-1 text-lg font-bold text-white">
                {lastPlan.departure} → {lastPlan.destination} corridor forecast
              </h2>
            </div>
            <StatusPill status="Generated" />
          </div>

          <div className="mt-5 space-y-6">
            <RouteDiagram
              origin={{ code: lastPlan.departure, city: originInfo.country ? `${originInfo.city}, ${originInfo.country}` : originInfo.city }}
              destination={{ code: lastPlan.destination, city: destInfo.country ? `${destInfo.city}, ${destInfo.country}` : destInfo.city }}
              caption={`${originInfo.city} to ${destInfo.city} route overview`} />
            
            <div className="w-full h-[400px] rounded-md border border-lineStrong overflow-hidden relative">
              <iframe
                src={mapUrl}
                width="100%"
                height="100%"
                style={{ border: 0 }}
                title="Aviation Weather & Wind Map"
                className="absolute inset-0"
                allowFullScreen
              ></iframe>
            </div>

            <div className="flex justify-end mt-4">
              <a
                href={`https://www.flightradar24.com/${originInfo.lat},${originInfo.lon}/6`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-lg bg-panel border border-line px-4 py-2 text-sm font-semibold text-white transition-colors duration-150 hover:bg-line-soft focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-bright"
              >
                Track Live on FlightRadar24 ↗
              </a>
            </div>
            
          </div>
        </section>
      )}
    </div>);

}