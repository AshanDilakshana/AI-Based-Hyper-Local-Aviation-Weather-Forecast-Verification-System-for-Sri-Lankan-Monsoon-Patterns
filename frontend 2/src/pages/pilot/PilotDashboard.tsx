import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusIcon } from 'lucide-react';
import { LiveFeedBadge, PageHeading } from '../../components/pilot/PageHeading';
import { StatCard } from '../../components/pilot/StatCard';
import { RouteDiagram } from '../../components/pilot/RouteDiagram';
import { StatusPill } from '../../components/pilot/StatusPill';
import { flightStats, routeMapImage } from '../../data/flight';
import { useAuth } from '../../contexts/AuthContext';

export function PilotDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();

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
          {flightStats.map((stat) =>
          <StatCard key={stat.label} {...stat} />
          )}
        </div>
      </section>

      <section className="rounded-xl border border-line bg-panel p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-sky-bright">
              Aviation weather briefing
            </p>
            <h2 className="mt-1 text-lg font-bold text-white">VCBI → WSSS corridor forecast</h2>
          </div>
          <StatusPill status="Draft" />
        </div>

        <div className="mt-5 space-y-6">
          <RouteDiagram
            origin={{ code: 'VCBI', city: 'Colombo' }}
            destination={{ code: 'WSSS', city: 'Singapore' }}
            caption="Indian Ocean route overview · FL350" />
          
          <img
            src={routeMapImage}
            alt="Map of the CMB to SIN flight track across the Indian Ocean"
            className="w-full rounded-md border border-lineStrong object-cover" />
          
        </div>
      </section>
    </div>);

}