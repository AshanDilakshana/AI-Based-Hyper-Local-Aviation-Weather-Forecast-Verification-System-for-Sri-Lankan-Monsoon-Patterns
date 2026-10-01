import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { PageHeading } from '../../components/pilot/PageHeading';
import { SearchIcon, FilterIcon, RefreshCwIcon } from 'lucide-react';

interface LogEntry {
  id: number;
  timestamp_utc: string;
  level: string;
  component: string;
  message: string;
  details: string | null;
}

export function SystemLogs() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState('all');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await axios.get('http://localhost:8000/admin/logs');
      setLogs(res.data);
    } catch (err) {
      console.error("Failed to fetch logs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchLogs(); }, []);

  const filtered = useMemo(() => {
    let list = [...logs];
    if (levelFilter !== 'all') {
      list = list.filter(l => l.level.toLowerCase() === levelFilter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(l =>
        l.message.toLowerCase().includes(q) ||
        l.component.toLowerCase().includes(q) ||
        l.level.toLowerCase().includes(q)
      );
    }
    return list;
  }, [logs, search, levelFilter]);

  const levelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error': return { bg: 'bg-rose-900/30', text: 'text-rose-400', border: 'border-rose-800/50' };
      case 'warning': return { bg: 'bg-amber-900/30', text: 'text-amber-400', border: 'border-amber-800/50' };
      case 'success': return { bg: 'bg-emerald-900/30', text: 'text-emerald-400', border: 'border-emerald-800/50' };
      default: return { bg: 'bg-sky-900/30', text: 'text-sky-400', border: 'border-sky-800/50' };
    }
  };

  const uniqueLevels = useMemo(() => {
    const set = new Set(logs.map(l => l.level.toLowerCase()));
    return Array.from(set).sort();
  }, [logs]);

  return (
    <div className="w-full space-y-6">
      <PageHeading
        eyebrow="Admin Portal"
        title="System Logs"
        description="View all system activity logs — user actions, bulk uploads, route changes, and more."
      />

      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="flex items-center gap-3 flex-1">
          <div className="relative w-full sm:w-80">
            <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input type="text" placeholder="Search logs..."
              value={search} onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-lg border border-line bg-ink pl-10 pr-4 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-accent placeholder:text-slate-500" />
          </div>
          <div className="flex items-center gap-2">
            <FilterIcon className="h-4 w-4 text-slate-500" />
            <select value={levelFilter} onChange={(e) => setLevelFilter(e.target.value)}
              className="rounded-lg border border-line bg-ink px-3 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-accent">
              <option value="all">All Levels</option>
              {uniqueLevels.map(l => (
                <option key={l} value={l}>{l.charAt(0).toUpperCase() + l.slice(1)}</option>
              ))}
            </select>
          </div>
        </div>
        <button onClick={fetchLogs}
          className="flex items-center gap-2 rounded-lg border border-line bg-panel px-4 py-2 text-sm font-semibold text-slate-300 transition-colors hover:border-accent hover:text-white">
          <RefreshCwIcon className="h-4 w-4" /> Refresh
        </button>
      </div>

      <p className="text-xs text-slate-500">Showing {filtered.length} of {logs.length} log entries</p>

      <section className="rounded-xl border border-line bg-panel p-5">
        {loading ? (
          <p className="py-10 text-center text-sm text-slate-400">Loading logs...</p>
        ) : filtered.length === 0 ? (
          <p className="py-10 text-center text-sm text-slate-400">
            {logs.length === 0 ? 'No system logs found.' : 'No logs match your filter.'}
          </p>
        ) : (
          <div className="space-y-2 max-h-[70vh] overflow-y-auto">
            {filtered.map((log) => {
              const lc = levelColor(log.level);
              return (
                <div key={log.id} className="flex items-start gap-3 rounded-lg border border-line/50 bg-ink/30 px-4 py-3 transition-colors hover:bg-slate-800/20">
                  <span className={`mt-0.5 shrink-0 rounded px-2 py-0.5 text-[10px] font-bold uppercase ${lc.bg} ${lc.text} border ${lc.border}`}>
                    {log.level}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-slate-200">{log.message}</p>
                    <div className="mt-1 flex items-center gap-3 text-[11px] text-slate-500">
                      <span className="font-mono">{log.component}</span>
                      <span>•</span>
                      <span>{new Date(log.timestamp_utc).toLocaleString()}</span>
                    </div>
                    {log.details && (
                      <pre className="mt-2 rounded bg-slate-900 p-2 text-[11px] text-slate-400 overflow-x-auto border border-line/30">
                        {log.details}
                      </pre>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
