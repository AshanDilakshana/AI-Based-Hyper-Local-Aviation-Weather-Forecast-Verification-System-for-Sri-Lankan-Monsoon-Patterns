import React, { useState, useEffect, useRef, useMemo } from 'react';
import axios from 'axios';
import { PageHeading } from '../../components/pilot/PageHeading';
import { UploadIcon, PlusIcon, TrashIcon, Edit2Icon, XIcon, CheckIcon, SearchIcon, AlertTriangleIcon } from 'lucide-react';

interface FlightSchedule {
  id: number;
  flight: string | null;
  departure_time_local: string | null;
  destination: string | null;
  time_period_mins: number | null;
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

export function FlightSchedules() {
  const [flights, setFlights] = useState<FlightSchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [search, setSearch] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingFlight, setEditingFlight] = useState<FlightSchedule | null>(null);
  const [formData, setFormData] = useState({
    flight: '',
    departure_time_local: '',
    destination: '',
    time_period_mins: 0
  });

  // Confirm dialog state
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmAction, setConfirmAction] = useState<(() => void) | null>(null);
  const [confirmTitle, setConfirmTitle] = useState('');
  const [confirmMsg, setConfirmMsg] = useState('');

  const showConfirm = (title: string, msg: string, action: () => void) => {
    setConfirmTitle(title);
    setConfirmMsg(msg);
    setConfirmAction(() => action);
    setConfirmOpen(true);
  };

  const fetchFlights = async () => {
    setLoading(true);
    try {
      const res = await axios.get('http://localhost:8000/admin/flights');
      setFlights(res.data);
    } catch (err) {
      console.error("Failed to fetch flights", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchFlights(); }, []);

  /* ── Sort: rows with flight data first, then by departure time ── */
  const sortedAndFiltered = useMemo(() => {
    let list = [...flights];
    // Sort: filled rows first, then by departure_time_local
    list.sort((a, b) => {
      const aHas = a.flight ? 1 : 0;
      const bHas = b.flight ? 1 : 0;
      if (aHas !== bHas) return bHas - aHas; // filled first
      // Both filled or both empty — sort by departure time
      const aTime = a.departure_time_local || 'zz';
      const bTime = b.departure_time_local || 'zz';
      return aTime.localeCompare(bTime);
    });
    // Search filter
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(f =>
        (f.flight && f.flight.toLowerCase().includes(q)) ||
        (f.destination && f.destination.toLowerCase().includes(q)) ||
        (f.departure_time_local && f.departure_time_local.includes(q)) ||
        String(f.time_period_mins).includes(q)
      );
    }
    return list;
  }, [flights, search]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const fd = new FormData();
    fd.append('file', file);

    setUploading(true);
    try {
      await axios.post('http://localhost:8000/admin/flights/bulk-upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      alert('Bulk upload successful!');
      fetchFlights();
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || 'Failed to upload file.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = (id: number) => {
    showConfirm('Delete Flight', 'Are you sure you want to permanently delete this flight schedule?', async () => {
      try {
        await axios.delete(`http://localhost:8000/admin/flights/${id}`);
        fetchFlights();
      } catch (err) {
        console.error(err);
        alert("Failed to delete flight.");
      }
    });
  };

  const openModal = (flight: FlightSchedule | null = null) => {
    if (flight) {
      setEditingFlight(flight);
      setFormData({
        flight: flight.flight || '',
        departure_time_local: flight.departure_time_local || '',
        destination: flight.destination || '',
        time_period_mins: flight.time_period_mins || 0
      });
    } else {
      setEditingFlight(null);
      setFormData({ flight: '', departure_time_local: '', destination: '', time_period_mins: 0 });
    }
    setIsModalOpen(true);
  };

  const closeModal = () => { setIsModalOpen(false); setEditingFlight(null); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingFlight) {
        await axios.put(`http://localhost:8000/admin/flights/${editingFlight.id}`, formData);
      } else {
        await axios.post('http://localhost:8000/admin/flights', formData);
      }
      closeModal();
      fetchFlights();
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || "An error occurred while saving the flight.");
    }
  };

  return (
    <div className="w-full space-y-6">
      <PageHeading
        eyebrow="Admin Portal"
        title="Flight Schedules"
        description="Manage daily active flight schedules and bulk upload routes via Excel/CSV."
      />

      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        {/* Search */}
        <div className="relative w-full sm:w-80">
          <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search flights, destinations..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-line bg-ink pl-10 pr-4 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-accent placeholder:text-slate-500"
          />
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => openModal()}
            className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-sky-500"
          >
            <PlusIcon className="h-4 w-4" />
            Add Flight
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="flex items-center gap-2 rounded-lg border border-line bg-panel px-4 py-2 text-sm font-semibold text-slate-300 transition-colors hover:border-accent hover:text-white disabled:opacity-50"
          >
            <UploadIcon className="h-4 w-4" />
            {uploading ? 'Uploading...' : 'Bulk Upload'}
          </button>
        </div>
      </div>

      {/* Counter */}
      <p className="text-xs text-slate-500">
        Showing {sortedAndFiltered.length} of {flights.length} flights
      </p>

      <section className="rounded-xl border border-line bg-panel p-5">
        {loading ? (
          <p className="py-10 text-center text-sm text-slate-400">Loading flights...</p>
        ) : sortedAndFiltered.length === 0 ? (
          <p className="py-10 text-center text-sm text-slate-400">
            {flights.length === 0 ? 'No flights found. Add some manually or bulk upload.' : 'No flights match your search.'}
          </p>
        ) : (
          <div className="overflow-x-auto max-h-[65vh] overflow-y-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="border-b border-line bg-slate-900/40 text-xs uppercase tracking-wider text-slate-400 sticky top-0 z-10">
                <tr>
                  <th className="px-4 py-3 font-semibold">ID</th>
                  <th className="px-4 py-3 font-semibold">Flight No</th>
                  <th className="px-4 py-3 font-semibold">Departure Time</th>
                  <th className="px-4 py-3 font-semibold">Destination</th>
                  <th className="px-4 py-3 font-semibold">Duration (Mins)</th>
                  <th className="px-4 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line/60">
                {sortedAndFiltered.map((flight) => (
                  <tr key={flight.id} className={`transition-colors hover:bg-slate-800/30 ${!flight.flight ? 'opacity-40' : ''}`}>
                    <td className="whitespace-nowrap px-4 py-3.5 text-xs text-slate-500">{flight.id}</td>
                    <td className="whitespace-nowrap px-4 py-3.5 font-mono text-sky-bright font-bold">
                      {flight.flight || <span className="text-slate-600 italic">empty</span>}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3.5 font-medium text-slate-200">
                      {flight.departure_time_local ? `${flight.departure_time_local} Local` : <span className="text-slate-600">-</span>}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3.5">
                      {flight.destination ? (
                        <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-300 border border-slate-700">
                          {flight.destination}
                        </span>
                      ) : <span className="text-slate-600">-</span>}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3.5 text-slate-300">
                      {flight.time_period_mins != null ? `${flight.time_period_mins} mins` : '-'}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3.5 text-right space-x-2">
                      <button
                        onClick={() => openModal(flight)}
                        className="rounded p-1.5 text-slate-400 hover:bg-slate-800 hover:text-sky-400 transition-colors"
                        title="Edit Flight"
                      >
                        <Edit2Icon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(flight.id)}
                        className="rounded p-1.5 text-slate-400 hover:bg-rose-900/50 hover:text-rose-400 transition-colors"
                        title="Delete Flight"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Edit/Add Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 px-4 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md rounded-2xl border border-line bg-panel p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-white">
                {editingFlight ? 'Edit Flight' : 'Add New Flight'}
              </h3>
              <button onClick={closeModal} className="text-slate-400 hover:text-white transition-colors">
                <XIcon className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Flight Number (e.g. UL604)</label>
                <input required type="text" value={formData.flight}
                  onChange={(e) => setFormData({...formData, flight: e.target.value})}
                  className="w-full rounded-lg border border-line bg-ink px-4 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Departure Time Local (e.g. 00:25)</label>
                <input required type="text" value={formData.departure_time_local}
                  onChange={(e) => setFormData({...formData, departure_time_local: e.target.value})}
                  className="w-full rounded-lg border border-line bg-ink px-4 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Destination ICAO/IATA (e.g. MEL)</label>
                <input required type="text" value={formData.destination}
                  onChange={(e) => setFormData({...formData, destination: e.target.value})}
                  className="w-full rounded-lg border border-line bg-ink px-4 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-accent" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Duration in Mins (e.g. 580)</label>
                <input required type="number" value={formData.time_period_mins}
                  onChange={(e) => setFormData({...formData, time_period_mins: parseInt(e.target.value) || 0})}
                  className="w-full rounded-lg border border-line bg-ink px-4 py-2.5 text-sm text-slate-200 outline-none transition-colors focus:border-accent" />
              </div>
              <div className="mt-6 flex justify-end gap-3 border-t border-line pt-4">
                <button type="button" onClick={closeModal}
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

      {/* Confirm Dialog */}
      <ConfirmDialog
        open={confirmOpen}
        title={confirmTitle}
        message={confirmMsg}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={() => { confirmAction?.(); setConfirmOpen(false); }}
      />
    </div>
  );
}
