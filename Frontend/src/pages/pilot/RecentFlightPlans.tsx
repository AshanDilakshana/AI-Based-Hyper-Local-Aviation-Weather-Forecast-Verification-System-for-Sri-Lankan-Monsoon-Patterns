import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { PageHeading, LiveFeedBadge } from '../../components/pilot/PageHeading';

interface FlightPlanRecord {
  id: number;
  pilot_reference: string;
  flight_no: string;
  departure: string;
  destination: string;
  departure_time: string;
  duration_mins: number;
  created_at: string;
}

export function RecentFlightPlans() {
  const { user } = useAuth();
  const [plans, setPlans] = useState<FlightPlanRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      axios.get(`http://localhost:8000/pilot/flight-plans?pilot_reference=${user.reference || 'guest'}`)
        .then(res => setPlans(res.data))
        .catch(err => console.error("Error fetching recent flight plans", err))
        .finally(() => setLoading(false));
    }
  }, [user]);

  const formatDateTime = (dateString: string) => {
    const d = new Date(dateString);
    return d.toLocaleString('en-GB', { 
      day: '2-digit', month: 'short', year: 'numeric', 
      hour: '2-digit', minute: '2-digit' 
    });
  };

  return (
    <div className="w-full space-y-6">
      <PageHeading
        eyebrow="Flight Operations"
        title="Recent Flight Plans"
        description="View your historical flight planning requests and routes."
        aside={<LiveFeedBadge />}
      />

      <section className="rounded-xl border border-line bg-panel p-5">
        <div className="mb-4">
          <h2 className="text-lg font-bold text-white">Flight Planning History</h2>
        </div>
        {loading ? (
          <p className="py-10 text-center text-sm text-slate-400">Loading flight plans...</p>
        ) : plans.length === 0 ? (
          <p className="py-10 text-center text-sm text-slate-400">No flight plans found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="border-b border-line bg-slate-900/40 text-xs uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="px-4 py-3 font-semibold">Created At</th>
                  <th className="px-4 py-3 font-semibold">Route</th>
                  <th className="px-4 py-3 font-semibold">Flight No</th>
                  <th className="px-4 py-3 font-semibold">Dep Time</th>
                  <th className="px-4 py-3 font-semibold">Duration (Mins)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/60">
                {plans.map((plan) => (
                  <tr key={plan.id} className="transition-colors hover:bg-slate-800/30">
                    <td className="whitespace-nowrap px-4 py-3.5 text-xs text-slate-400">
                      {formatDateTime(plan.created_at)}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3.5 font-medium text-slate-200">
                      <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-300 border border-slate-700">
                        {plan.departure} → {plan.destination}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3.5 font-mono text-sky-bright">
                      {plan.flight_no || 'N/A'}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3.5 text-xs text-slate-400">
                      {formatDateTime(plan.departure_time)}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3.5 text-slate-300">
                      {plan.duration_mins}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
