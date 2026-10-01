import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { PageHeading } from '../../components/pilot/PageHeading';
import { PlusIcon, Edit2Icon, TrashIcon, XIcon, CheckIcon, AlertTriangleIcon, MapPinIcon, SearchIcon } from 'lucide-react';

interface RouteAlt {
  id: number;
  region_name: string;
  airports: string;
}

/* ── Confirmation Dialog ──────────────────────────────────────────── */
function ConfirmDialog({ open, title, message, onConfirm, onCancel }: {
  open: boolean; title: string; message: string; onConfirm: () => void; onCancel: () => void;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/80 px-4 backdrop-blur-sm">
      <div className="w-full max-w-sm rounded-2xl border border-rose-900/60 bg-panel p-6 shadow-2xl">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-rose-900/30">
            <AlertTriangleIcon className="h-5 w-5 text-rose-400" />
          </div>
          <h3 className="text-lg font-bold text-white">{title}</h3>
        </div>
        <p className="text-sm text-slate-300 mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button onClick={onCancel} className="rounded-lg px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800 transition-colors">Cancel</button>
          <button onClick={onConfirm} className="rounded-lg bg-rose-600 px-5 py-2 text-sm font-semibold text-white hover:bg-rose-500 transition-colors">Confirm</button>
        </div>
      </div>
    </div>
  );
}

export function RouteAlternatives() {
  const [routes, setRoutes] = useState<RouteAlt[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editRoute, setEditRoute] = useState<RouteAlt | null>(null);
  const [formData, setFormData] = useState({ region_name: '', airports: '' });

  // Confirm state
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmAction, setConfirmAction] = useState<(() => void) | null>(null);
  const [confirmTitle, setConfirmTitle] = useState('');
  const [confirmMsg, setConfirmMsg] = useState('');

  const showConfirm = (title: string, msg: string, action: () => void) => {
    setConfirmTitle(title); setConfirmMsg(msg); setConfirmAction(() => action); setConfirmOpen(true);
  };

  const fetchRoutes = async () => {
    setLoading(true);
    try {
      const res = await axios.get('http://localhost:8000/admin/routes');
      setRoutes(res.data);
    } catch (err) {
      console.error("Failed to fetch routes", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRoutes(); }, []);

  const filtered = search.trim()
    ? routes.filter(r =>
        r.region_name.toLowerCase().includes(search.toLowerCase()) ||
        r.airports.toLowerCase().includes(search.toLowerCase())
      )
    : routes;

  const openModal = (route: RouteAlt | null = null) => {
    if (route) {
      setEditRoute(route);
      setFormData({ region_name: route.region_name, airports: route.airports });
    } else {
      setEditRoute(null);
      setFormData({ region_name: '', airports: '' });
    }
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editRoute) {
        await axios.put(`http://localhost:8000/admin/routes/${editRoute.id}`, formData);
      } else {
        await axios.post('http://localhost:8000/admin/routes', formData);
      }
      setIsModalOpen(false);
      setEditRoute(null);
      fetchRoutes();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Error saving route.");
    }
  };

  const handleDelete = (route: RouteAlt) => {
    showConfirm('Delete Route Region', `Are you sure you want to delete "${route.region_name}"? This will remove all associated airports.`, async () => {
      try {
        await axios.delete(`http://localhost:8000/admin/routes/${route.id}`);
        fetchRoutes();
      } catch (err: any) {
        alert(err.response?.data?.detail || "Failed to delete route.");
      }
    });
  };

  return (
    <div className="w-full space-y-6">
      <PageHeading
        eyebrow="Admin Portal"
        title="Route Alternatives"
        description="Manage route regions and their alternative airports for weather-based rerouting."
      />

      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative w-full sm:w-80">
          <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input type="text" placeholder="Search regions or airports..."
            value={search} onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-line bg-ink pl-10 pr-4 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-accent placeholder:text-slate-500" />
        </div>
        <button onClick={() => openModal()}
          className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-sky-500">
          <PlusIcon className="h-4 w-4" /> Add Region
        </button>
      </div>

      <p className="text-xs text-slate-500">Showing {filtered.length} of {routes.length} route regions</p>

      <section className="rounded-xl border border-line bg-panel p-5">
        {loading ? (
          <p className="py-10 text-center text-sm text-slate-400">Loading routes...</p>
        ) : filtered.length === 0 ? (
          <p className="py-10 text-center text-sm text-slate-400">
            {routes.length === 0 ? 'No route regions found. Add one to get started.' : 'No routes match your search.'}
          </p>
        ) : (
          <div className="space-y-3">
            {filtered.map((route) => (
              <div key={route.id} className="flex items-start justify-between rounded-lg border border-line/50 bg-ink/30 p-4 transition-colors hover:bg-slate-800/30">
                <div className="flex items-start gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-900/30 border border-violet-800/50 mt-0.5">
                    <MapPinIcon className="h-4 w-4 text-violet-400" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-white">{route.region_name}</p>
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {route.airports.split(',').map((a) => a.trim()).filter(Boolean).map((airport) => (
                        <span key={airport} className="rounded bg-slate-800 px-2 py-0.5 text-xs font-mono text-sky-300 border border-slate-700">
                          {airport}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0 ml-4">
                  <button onClick={() => openModal(route)}
                    className="rounded p-1.5 text-slate-400 hover:bg-slate-800 hover:text-sky-400 transition-colors" title="Edit">
                    <Edit2Icon className="h-4 w-4" />
                  </button>
                  <button onClick={() => handleDelete(route)}
                    className="rounded p-1.5 text-slate-400 hover:bg-rose-900/50 hover:text-rose-400 transition-colors" title="Delete">
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Add/Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 px-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-line bg-panel p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-white">{editRoute ? 'Edit Route Region' : 'Add New Region'}</h3>
              <button onClick={() => { setIsModalOpen(false); setEditRoute(null); }} className="text-slate-400 hover:text-white transition-colors">
                <XIcon className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Region Name (e.g. South East Asia)</label>
                <input required type="text" value={formData.region_name}
                  onChange={(e) => setFormData({...formData, region_name: e.target.value})}
                  className="w-full rounded-lg border border-line bg-ink px-4 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Airports (comma-separated ICAO codes)</label>
                <textarea required rows={3} value={formData.airports}
                  onChange={(e) => setFormData({...formData, airports: e.target.value})}
                  placeholder="e.g. WSSS, VTBS, VDPP, WMKK"
                  className="w-full rounded-lg border border-line bg-ink px-4 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-accent placeholder:text-slate-500 resize-none" />
                <p className="mt-1 text-[11px] text-slate-500">Separate each ICAO code with a comma</p>
              </div>
              <div className="mt-6 flex justify-end gap-3 border-t border-line pt-4">
                <button type="button" onClick={() => { setIsModalOpen(false); setEditRoute(null); }}
                  className="rounded-lg px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800 transition-colors">Cancel</button>
                <button type="submit"
                  className="flex items-center gap-2 rounded-lg bg-accent px-5 py-2 text-sm font-semibold text-white hover:bg-sky-500 transition-colors">
                  <CheckIcon className="h-4 w-4" /> Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <ConfirmDialog open={confirmOpen} title={confirmTitle} message={confirmMsg}
        onCancel={() => setConfirmOpen(false)} onConfirm={() => { confirmAction?.(); setConfirmOpen(false); }} />
    </div>
  );
}
