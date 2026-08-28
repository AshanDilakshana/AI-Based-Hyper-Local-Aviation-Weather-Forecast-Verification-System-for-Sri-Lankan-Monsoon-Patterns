import React, { useState } from 'react';
import axios from 'axios';
import { CheckCircle2Icon, XIcon, SaveIcon } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

interface UploadPreviewModalProps {
  records: any[];
  onClose: () => void;
  onSuccess: () => void;
}

export function UploadPreviewModal({ records: initialRecords, onClose, onSuccess }: UploadPreviewModalProps) {
  const [records, setRecords] = useState(initialRecords);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpdate = (index: number, field: string, value: string) => {
    const updated = [...records];
    let val: any = value;
    if (field !== 'target_time' && field !== 'remarks' && value !== '') {
      val = parseFloat(value);
      if (isNaN(val)) val = '';
    }
    updated[index] = { ...updated[index], [field]: val };
    setRecords(updated);
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      // Filter out any invalid rows if needed
      const payload = records.map(r => {
          const req: any = { target_time: r.target_time };
          if (r.dry_temp_c !== null && r.dry_temp_c !== '') req.dry_temp_c = r.dry_temp_c;
          if (r.qnh_hpa !== null && r.qnh_hpa !== '') req.qnh_hpa = r.qnh_hpa;
          if (r.wind_dir !== null && r.wind_dir !== '') req.wind_dir = r.wind_dir;
          if (r.wind_speed_kts !== null && r.wind_speed_kts !== '') req.wind_speed_kts = r.wind_speed_kts;
          if (r.remarks !== null && r.remarks !== '') req.remarks = r.remarks;
          return req;
      });
      
      await axios.post(`${API_BASE}/forecasts/bulk-verify`, { forecasts: payload });
      onSuccess();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((e: any) => e.msg + (e.loc ? ` (${e.loc.join('.')})` : '')).join(', '));
      } else {
        setError(detail ? JSON.stringify(detail) : "Error saving records");
      }
      setSaving(false);
    }
  };

  const formatIsoToAviationTime = (isoString: string) => {
    if (!isoString) return '--';
    const d = new Date(isoString);
    const dd = d.getUTCDate().toString().padStart(2, '0');
    const hh = d.getUTCHours().toString().padStart(2, '0');
    const mm = d.getUTCMinutes().toString().padStart(2, '0');
    return `${dd}${hh}${mm}Z`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-panel w-full max-w-4xl max-h-[90vh] rounded-xl border border-line-strong flex flex-col shadow-2xl">
        
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-line-strong">
          <div>
            <h2 className="text-lg font-bold text-white">Review Extracted Data</h2>
            <p className="text-xs text-slate-400 mt-1">
              Edit any values below before saving. These records will be saved as verified forecasts and will overwrite existing data for the same target times.
            </p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <XIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Content Table */}
        <div className="flex-1 overflow-auto p-5">
          {error && (
            <div className="mb-4 p-3 rounded-lg border border-red-500/40 bg-red-500/10 text-sm text-red-400">
              {error}
            </div>
          )}
          
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="text-xs text-slate-500 sticky top-0 bg-panel z-10">
              <tr>
                <th className="pb-3 pr-4 font-medium">Target Time</th>
                <th className="pb-3 pr-4 font-medium">Wind Dir (°)</th>
                <th className="pb-3 pr-4 font-medium">Wind Spd (kt)</th>
                <th className="pb-3 pr-4 font-medium">Temp (°C)</th>
                <th className="pb-3 pr-4 font-medium">QNH (hPa)</th>
                <th className="pb-3 pr-4 font-medium">Remarks</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line-strong">
              {records.map((r, i) => (
                <tr key={i} className="hover:bg-ink/50 transition-colors">
                  <td className="py-2 pr-4 font-mono text-slate-200">
                    {formatIsoToAviationTime(r.target_time)}
                  </td>
                  <td className="py-2 pr-4">
                    <input 
                      type="number" 
                      value={r.wind_dir ?? ''} 
                      onChange={e => handleUpdate(i, 'wind_dir', e.target.value)}
                      className="w-16 bg-ink border border-line-strong rounded px-2 py-1 text-sm outline-none focus:border-accent"
                    />
                  </td>
                  <td className="py-2 pr-4">
                    <input 
                      type="number" 
                      value={r.wind_speed_kts ?? ''} 
                      onChange={e => handleUpdate(i, 'wind_speed_kts', e.target.value)}
                      className="w-16 bg-ink border border-line-strong rounded px-2 py-1 text-sm outline-none focus:border-accent"
                    />
                  </td>
                  <td className="py-2 pr-4">
                    <input 
                      type="number" 
                      value={r.dry_temp_c ?? ''} 
                      onChange={e => handleUpdate(i, 'dry_temp_c', e.target.value)}
                      className="w-16 bg-ink border border-line-strong rounded px-2 py-1 text-sm outline-none focus:border-accent"
                    />
                  </td>
                  <td className="py-2 pr-4">
                    <input 
                      type="number" 
                      value={r.qnh_hpa ?? ''} 
                      onChange={e => handleUpdate(i, 'qnh_hpa', e.target.value)}
                      className="w-20 bg-ink border border-line-strong rounded px-2 py-1 text-sm outline-none focus:border-accent"
                    />
                  </td>
                  <td className="py-2 pr-4">
                    <input 
                      type="text" 
                      value={r.remarks || ''} 
                      onChange={e => handleUpdate(i, 'remarks', e.target.value)}
                      className="w-full bg-ink border border-line-strong rounded px-2 py-1 text-sm outline-none focus:border-accent"
                      placeholder="PROB30 SHRA"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-5 border-t border-line-strong bg-ink/50 rounded-b-xl">
          <button
            onClick={onClose}
            disabled={saving}
            className="px-4 py-2 text-sm font-semibold text-slate-300 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-70 text-white px-5 py-2 rounded-lg text-sm font-bold transition-colors shadow-lg shadow-emerald-500/20"
          >
            <SaveIcon className="w-4 h-4" />
            {saving ? 'Saving...' : 'Confirm & Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
