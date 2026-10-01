import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { PageHeading } from '../../components/pilot/PageHeading';
import { UsersIcon, PlaneIcon, MapIcon, ActivityIcon, ShieldCheckIcon, ShieldAlertIcon, ArrowRightIcon } from 'lucide-react';

interface DashboardStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  total_flights: number;
  total_routes: number;
  recent_logs: Array<{
    id: number;
    timestamp_utc: string;
    level: string;
    component: string;
    message: string;
  }>;
}

export function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get('http://localhost:8000/admin/stats')
      .then(res => setStats(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const cards = stats ? [
    { label: 'Total Users', value: stats.total_users, icon: UsersIcon, color: 'sky', link: '/admin/users' },
    { label: 'Active Users', value: stats.active_users, icon: ShieldCheckIcon, color: 'emerald', link: '/admin/users' },
    { label: 'Inactive Users', value: stats.inactive_users, icon: ShieldAlertIcon, color: 'rose', link: '/admin/users' },
    { label: 'Flight Schedules', value: stats.total_flights, icon: PlaneIcon, color: 'amber', link: '/admin/flights' },
    { label: 'Route Regions', value: stats.total_routes, icon: MapIcon, color: 'violet', link: '/admin/routes' },
  ] : [];

  const colorMap: Record<string, { statClass: string; text: string; icon: string }> = {
    sky:     { statClass: 'stat-sky',     text: 'text-sky-600',     icon: 'text-sky-500' },
    emerald: { statClass: 'stat-emerald', text: 'text-emerald-600', icon: 'text-emerald-500' },
    rose:    { statClass: 'stat-rose',    text: 'text-rose-600',    icon: 'text-rose-500' },
    amber:   { statClass: 'stat-amber',   text: 'text-amber-600',   icon: 'text-amber-500' },
    violet:  { statClass: 'stat-violet',  text: 'text-violet-600',  icon: 'text-violet-500' },
  };

  const levelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error': return 'text-rose-500';
      case 'warning': return 'text-amber-500';
      case 'success': return 'text-emerald-500';
      default: return 'text-sky-500';
    }
  };

  return (
    <div className="w-full space-y-6">
      <PageHeading
        eyebrow="Admin Portal"
        title="Dashboard"
        description="System overview — users, flights, routes, and recent activity."
      />

      {loading ? (
        <p className="py-10 text-center text-sm text-slate-400">Loading dashboard...</p>
      ) : stats ? (
        <>
          {/* Stat Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {cards.map((card) => {
              const c = colorMap[card.color];
              return (
                <button
                  key={card.label}
                  onClick={() => navigate(card.link)}
                  className={`group rounded-xl border ${c.statClass} p-5 text-left transition-all hover:scale-[1.02] hover:shadow-lg`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <card.icon className={`h-5 w-5 ${c.icon}`} />
                    <ArrowRightIcon className="h-4 w-4 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                  <p className={`text-3xl font-bold ${c.text}`}>{card.value}</p>
                  <p className="mt-1 text-xs font-medium text-slate-400">{card.label}</p>
                </button>
              );
            })}
          </div>

          {/* Quick Links */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { label: 'Manage Users', desc: 'Activate, deactivate, edit user details', link: '/admin/users', Icon: UsersIcon },
              { label: 'Flight Schedules', desc: 'Add, edit, bulk upload flights', link: '/admin/flights', Icon: PlaneIcon },
              { label: 'Route Alternatives', desc: 'Manage route regions and airports', link: '/admin/routes', Icon: MapIcon },
            ].map((item) => (
              <button
                key={item.label}
                onClick={() => navigate(item.link)}
                className="group flex items-center gap-4 rounded-xl border border-line bg-panel p-5 text-left transition-all hover:border-accent/50 hover:bg-slate-800/30"
              >
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-accent/10 border border-accent/20">
                  <item.Icon className="h-6 w-6 text-accent" />
                </div>
                <div>
                  <p className="text-sm font-bold text-white group-hover:text-accent transition-colors">{item.label}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{item.desc}</p>
                </div>
              </button>
            ))}
          </div>

          {/* Recent Activity */}
          <section className="rounded-xl border border-line bg-panel p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <ActivityIcon className="h-4 w-4 text-accent" /> Recent System Activity
              </h3>
              <button onClick={() => navigate('/admin/logs')} className="text-xs text-accent hover:text-sky-300 transition-colors">
                View All Logs →
              </button>
            </div>
            {stats.recent_logs.length === 0 ? (
              <p className="text-sm text-slate-500 py-4 text-center">No recent system activity.</p>
            ) : (
              <div className="space-y-2">
                {stats.recent_logs.map((log) => (
                  <div key={log.id} className="flex items-start gap-3 rounded-lg border border-line/50 bg-ink/50 px-4 py-3">
                    <span className={`mt-0.5 text-[10px] font-bold uppercase ${levelColor(log.level)}`}>{log.level}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-200 truncate">{log.message}</p>
                      <p className="text-[11px] text-slate-500 mt-0.5">{log.component} — {new Date(log.timestamp_utc).toLocaleString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      ) : (
        <p className="text-sm text-rose-400">Failed to load dashboard data.</p>
      )}
    </div>
  );
}
