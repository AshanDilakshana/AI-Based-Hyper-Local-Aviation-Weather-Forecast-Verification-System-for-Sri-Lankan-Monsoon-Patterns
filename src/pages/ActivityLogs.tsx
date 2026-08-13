import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  ActivityIcon, 
  CheckCircle2Icon, 
  InfoIcon, 
  AlertTriangleIcon, 
  XCircleIcon, 
  RefreshCwIcon, 
  SearchIcon, 
  FilterIcon,
  ShieldCheckIcon,
  PlaneTakeoffIcon
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Panel } from '../components/ui/Panel';

const API_BASE = 'http://localhost:8000';

type LogItem = {
  id: number;
  timestamp_utc: string;
  level: 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR';
  component: string;
  message: string;
  details?: string;
};

export function ActivityLogs() {
  const { user } = useAuth();
  const isPilot = user?.role === 'pilot';

  const [logs, setLogs] = useState<LogItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [levelFilter, setLevelFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const roleParam = isPilot ? 'pilot' : 'forecaster';
      const levelParam = levelFilter !== 'ALL' ? levelFilter : '';
      const res = await axios.get(`${API_BASE}/logs?role=${roleParam}&level=${levelParam}`);
      setLogs(res.data);
    } catch (err) {
      console.error('Failed to fetch activity logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [user?.role, levelFilter]);

  const filteredLogs = logs.filter(log => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      log.message.toLowerCase().includes(q) ||
      log.component.toLowerCase().includes(q) ||
      (log.details && log.details.toLowerCase().includes(q))
    );
  });

  const getLevelBadge = (level: string) => {
    switch (level) {
      case 'SUCCESS':
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
            <CheckCircle2Icon className="h-3.5 w-3.5" />
            SUCCESS
          </span>
        );
      case 'WARNING':
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-400 border border-amber-500/20">
            <AlertTriangleIcon className="h-3.5 w-3.5" />
            WARNING
          </span>
        );
      case 'ERROR':
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-500/10 px-2.5 py-1 text-xs font-semibold text-rose-400 border border-rose-500/20">
            <XCircleIcon className="h-3.5 w-3.5" />
            ERROR
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-sky-500/10 px-2.5 py-1 text-xs font-semibold text-sky-400 border border-sky-500/20">
            <InfoIcon className="h-3.5 w-3.5" />
            INFO
          </span>
        );
    }
  };

  const formatLogTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      const dd = d.getUTCDate().toString().padStart(2, '0');
      const hh = d.getUTCHours().toString().padStart(2, '0');
      const mm = d.getUTCMinutes().toString().padStart(2, '0');
      const ss = d.getUTCSeconds().toString().padStart(2, '0');
      return `${dd}${hh}${mm}${ss}Z`;
    } catch {
      return isoString;
    }
  };

  const successCount = logs.filter(l => l.level === 'SUCCESS').length;
  const infoCount = logs.filter(l => l.level === 'INFO').length;
  const alertCount = logs.filter(l => l.level === 'WARNING' || l.level === 'ERROR').length;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 rounded-md bg-accent-soft/10 px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-accent-soft border border-accent-soft/20">
            {isPilot ? <PlaneTakeoffIcon className="h-3.5 w-3.5" /> : <ShieldCheckIcon className="h-3.5 w-3.5" />}
            {isPilot ? 'Pilot Activity Trail' : 'System Operational Logs'}
          </div>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">
            {isPilot ? 'My Activity & Flight Logs' : 'System & Audit Logs'}
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            {isPilot
              ? 'Authorized audit trail of your pre-flight briefings, corridor queries, and downloaded weather packages.'
              : 'Complete operational logs including MLOps model retraining, METAR ingestion, and forecaster verification history.'}
          </p>
        </div>
        <button
          type="button"
          onClick={fetchLogs}
          disabled={loading}
          className="inline-flex items-center gap-2 self-start rounded-lg border border-line-strong px-4 py-2.5 text-sm font-semibold text-slate-200 transition-colors hover:border-accent hover:text-white disabled:opacity-60">
          <RefreshCwIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Refreshing…' : 'Refresh Logs'}
        </button>
      </header>

      {/* Metric Summary Cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="rounded-xl border border-line bg-panel p-4">
          <p className="text-xs font-medium text-slate-400">Total Log Entries</p>
          <p className="mt-2 text-2xl font-bold text-white">{logs.length}</p>
          <p className="mt-1 text-[11px] text-slate-500">
            {isPilot ? 'Pilot-scoped records' : 'All system components'}
          </p>
        </div>
        <div className="rounded-xl border border-line bg-panel p-4">
          <p className="text-xs font-medium text-slate-400">Successful Events</p>
          <p className="mt-2 text-2xl font-bold text-emerald-400">{successCount}</p>
          <p className="mt-1 text-[11px] text-slate-500">Completed operations</p>
        </div>
        <div className="rounded-xl border border-line bg-panel p-4">
          <p className="text-xs font-medium text-slate-400">Informational Logs</p>
          <p className="mt-2 text-2xl font-bold text-sky-400">{infoCount}</p>
          <p className="mt-1 text-[11px] text-slate-500">Routine system events</p>
        </div>
        <div className="rounded-xl border border-line bg-panel p-4">
          <p className="text-xs font-medium text-slate-400">Warnings & Errors</p>
          <p className="mt-2 text-2xl font-bold text-amber-400">{alertCount}</p>
          <p className="mt-1 text-[11px] text-slate-500">Attention required</p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <Panel title="Filter & Search Logs">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative flex-1 max-w-md">
            <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by component, message or details..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-line bg-ink pl-9 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:border-accent focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-2">
            <FilterIcon className="h-4 w-4 text-slate-400" />
            <span className="text-xs font-semibold text-slate-400">Level:</span>
            {['ALL', 'SUCCESS', 'INFO', 'WARNING', 'ERROR'].map(lvl => (
              <button
                key={lvl}
                onClick={() => setLevelFilter(lvl)}
                className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-colors ${
                  levelFilter === lvl
                    ? 'bg-accent text-white'
                    : 'bg-ink border border-line text-slate-400 hover:text-white'
                }`}>
                {lvl}
              </button>
            ))}
          </div>
        </div>
      </Panel>

      {/* Main Logs Table */}
      <Panel
        title={isPilot ? "Activity Log Trail" : "System Log Feed"}
        subtitle={`Showing ${filteredLogs.length} of ${logs.length} logged events`}>
        
        {filteredLogs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center text-slate-400">
            <ActivityIcon className="h-10 w-10 text-slate-600 mb-3" />
            <p className="text-base font-semibold text-slate-300">No logs found matching your criteria</p>
            <p className="mt-1 text-xs text-slate-500">Try adjusting your search query or level filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="border-b border-line text-xs uppercase tracking-wider text-slate-400 bg-slate-900/40">
                <tr>
                  <th className="px-4 py-3 font-semibold">Time (UTC)</th>
                  <th className="px-4 py-3 font-semibold">Level</th>
                  <th className="px-4 py-3 font-semibold">Component</th>
                  <th className="px-4 py-3 font-semibold">Message</th>
                  <th className="px-4 py-3 font-semibold">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/60">
                {filteredLogs.map(log => (
                  <tr key={log.id} className="transition-colors hover:bg-slate-800/30">
                    <td className="px-4 py-3.5 font-mono text-xs text-slate-400 whitespace-nowrap">
                      {formatLogTime(log.timestamp_utc)}
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      {getLevelBadge(log.level)}
                    </td>
                    <td className="px-4 py-3.5 font-medium text-slate-200 whitespace-nowrap">
                      <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-300 border border-slate-700">
                        {log.component}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-slate-200">
                      {log.message}
                    </td>
                    <td className="px-4 py-3.5 text-xs text-slate-400 max-w-xs truncate">
                      {log.details ? (
                        <span className="font-mono bg-ink/80 px-2 py-1 rounded text-[11px] text-slate-300 border border-line inline-block">
                          {log.details}
                        </span>
                      ) : (
                        <span className="text-slate-600">--</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}
