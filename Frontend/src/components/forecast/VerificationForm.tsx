import React, { useState, useEffect } from 'react';
import { CalendarIcon, ClockIcon, CheckCircle2Icon, UploadIcon } from 'lucide-react';
import axios from 'axios';

type FieldState = {
  temperature: string;
  windSpeed: string;
  windDirection: string;
  humidity: string;
  cloudBase: string;
  visibility: string;
  pressure: string;
  targetTime: string;
  observedTime: string;
};

const formatToUtcDatetime = (d: Date) => {
  const pad = (n: number) => n.toString().padStart(2, '0');
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}T${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
};

const now = new Date();
const initialTarget = new Date();
initialTarget.setHours(now.getHours() + 3);

const initialState: FieldState = {
  temperature: '--',
  windSpeed: '--',
  windDirection: '--',
  humidity: '--',
  cloudBase: '--',
  visibility: '--',
  pressure: '--',
  targetTime: formatToUtcDatetime(initialTarget),
  observedTime: formatToUtcDatetime(now)
};

const numericFields: {key: keyof FieldState;label: string;suffix: string;}[] = [
{ key: 'temperature', label: 'Temperature', suffix: '°C' },
{ key: 'windSpeed', label: 'Wind speed', suffix: 'kt' },
{ key: 'windDirection', label: 'Wind direction', suffix: '°' },
{ key: 'humidity', label: 'Humidity', suffix: '% RH' },
{ key: 'cloudBase', label: 'Clouds', suffix: '' },
{ key: 'visibility', label: 'Visibility', suffix: 'km' },
{ key: 'pressure', label: 'Pressure', suffix: 'hPa' }];


export function VerificationForm({ onSaveSuccess, editData, prefillData }: { onSaveSuccess?: () => void, editData?: any, prefillData?: any }) {
  const [fields, setFields] = useState<FieldState>(initialState);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [blockTimer, setBlockTimer] = useState(0);

  useEffect(() => {
    if (blockTimer > 0) {
      const timer = setTimeout(() => setBlockTimer(blockTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [blockTimer]);

  useEffect(() => {
    if (editData) {
      setFields({
        ...initialState,
        targetTime: editData.target_time.substring(0, 16),
        temperature: editData.dry_temp_c?.toString() || '',
        windSpeed: editData.wind_speed_kts?.toString() || '',
        windDirection: editData.wind_dir?.toString() || '',
        humidity: editData.rh_percent?.toString() || '',
        cloudBase: editData.clouds || '',
        visibility: editData.visibility?.toString() || '',
        pressure: editData.qnh_hpa?.toString() || ''
      });
    } else if (prefillData) {
      setFields({
        ...initialState,
        temperature: prefillData.temperature_pressure_forecast?.prediction?.temperature_C?.toString() || '',
        windSpeed: prefillData.wind_forecast?.predicted_wind_speed_kts?.toString() || '',
        windDirection: prefillData.wind_forecast?.wind_dir?.toString() || '',
        humidity: prefillData.qnh_dewpoint_forecast?.derived_rh_3h?.toString() || '',
        cloudBase: prefillData.cloud_visibility_forecast?.cloud_status?.replace('_', ' ') || '',
        visibility: prefillData.cloud_visibility_forecast?.visibility_prediction ? (prefillData.cloud_visibility_forecast.visibility_prediction / 1000).toString() : '',
        pressure: prefillData.qnh_dewpoint_forecast?.predicted_qnh_3h?.toString() || (prefillData.temperature_pressure_forecast?.prediction?.pressure_hPa?.toString() || '')
      });
    }
  }, [editData, prefillData]);

  const update = (key: keyof FieldState, value: string) =>
    setFields((previous) => ({ ...previous, [key]: value }));

  const addThreeHours = () => {
    if (!fields.targetTime) return;
    const d = new Date(fields.targetTime + 'Z'); // parse as UTC
    d.setUTCHours(d.getUTCHours() + 3);
    update('targetTime', formatToUtcDatetime(d));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMessage('');
    try {
      const parseField = (val: string) => {
        if (val === '--' || val.trim() === '') return null;
        const parsed = parseFloat(val);
        return isNaN(parsed) ? null : parsed;
      };
      
      const windSpeed = parseField(fields.windSpeed);

      const payload = {
        target_time: new Date(fields.targetTime + 'Z').toISOString(),
        created_at: new Date(fields.observedTime + 'Z').toISOString(),
        dry_temp_c: parseField(fields.temperature),
        wind_speed_kts: windSpeed,
        wind_dir: parseField(fields.windDirection) !== null ? parseField(fields.windDirection) : 0,
        rh_percent: parseField(fields.humidity),
        clouds: fields.cloudBase === '--' ? null : fields.cloudBase,
        visibility: parseField(fields.visibility) !== null ? parseField(fields.visibility)! * 1000 : null,
        qnh_hpa: parseField(fields.pressure),
        headwind_kts: windSpeed !== null ? Math.round(windSpeed * Math.cos((40 * Math.PI) / 180)) : null,
        crosswind_kts: windSpeed !== null ? Math.round(windSpeed * Math.sin((40 * Math.PI) / 180)) : null
      };

      if (editData?.id) {
        await axios.put(`http://localhost:8000/forecasts/verify/${editData.id}`, payload);
        setSuccessMessage('Verified forecast updated successfully!');
      } else {
        await axios.post('http://localhost:8000/forecasts/verify', payload);
        setSuccessMessage('Verified forecast saved successfully!');
      }

      if (onSaveSuccess) onSaveSuccess();
      setBlockTimer(30);
      setTimeout(() => setSuccessMessage(''), 5000); // hide success message after 5s
    } catch (error) {
      console.error('Failed to save verified forecast', error);
      alert('Failed to save data. Please check backend logs.');
    } finally {
      setSaving(false);
    }
  };

  const showPicker = (id: string) => {
    const el = document.getElementById(id) as any;
    if (el && typeof el.showPicker === 'function') {
      el.showPicker();
    }
  };

  return (
    <form className="flex flex-col gap-6" onSubmit={handleSave}>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {numericFields.map(({ key, label, suffix }) =>
        <div key={key}>
            <label htmlFor={key} className="block text-xs text-slate-400">
              {label}
            </label>
            <div className="mt-2 flex items-center rounded-lg border border-line-strong bg-ink px-3 py-2.5 focus-within:border-accent">
              <input
              id={key}
              value={fields[key]}
              onChange={(event) => update(key, event.target.value)}
              inputMode={key === 'cloudBase' ? "text" : "decimal"}
              className="w-full bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-600" />
            
              {suffix && <span className="pl-2 text-xs text-slate-500">{suffix}</span>}
            </div>
          </div>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div>
          <label htmlFor="targetTime" className="block text-xs font-medium text-slate-400">
            Target time and date (UTC)
          </label>
          <div className="mt-2 flex items-center gap-3 rounded-lg border border-line-strong bg-ink px-3 py-3 focus-within:border-accent">
            <CalendarIcon 
              className="h-4 w-4 shrink-0 text-slate-500 cursor-pointer hover:text-slate-300" 
              aria-hidden="true" 
              onClick={() => {
                const el = document.getElementById('targetTime') as any;
                if (el) {
                  try { el.showPicker(); } catch (e) { el.focus(); }
                }
              }} 
            />
            <input
              id="targetTime"
              type="datetime-local"
              value={fields.targetTime}
              onChange={(event) => update('targetTime', event.target.value)}
              className="w-full bg-transparent text-sm text-slate-300 outline-none" />
            
            <button 
              type="button" 
              onClick={addThreeHours}
              className="rounded border border-line-strong px-2 py-0.5 text-[11px] font-bold text-slate-300 hover:bg-slate-800 focus:outline-none focus:ring-1 focus:ring-accent"
            >
              +3h
            </button>
          </div>
        </div>
        <div>
          <label htmlFor="observedTime" className="block text-xs font-medium text-slate-400">
            Time (Forecast Generated At UTC)
          </label>
          <div className="mt-2 flex items-center gap-3 rounded-lg border border-line-strong bg-ink px-3 py-3 focus-within:border-accent">
            <ClockIcon 
              className="h-4 w-4 shrink-0 text-slate-500 cursor-pointer hover:text-slate-300" 
              aria-hidden="true" 
              onClick={() => {
                const el = document.getElementById('observedTime') as any;
                if (el) {
                  try { el.showPicker(); } catch (e) { el.focus(); }
                }
              }} 
            />
            <input
              id="observedTime"
              type="datetime-local"
              value={fields.observedTime}
              onChange={(event) => update('observedTime', event.target.value)}
              className="w-full bg-transparent text-sm text-slate-300 outline-none" />
          </div>
        </div>
      </div>
      
      <div className="flex flex-col items-end gap-4 mt-2 w-full">
        {successMessage && (
          <div className="w-full flex items-center justify-between rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 shadow-[0_0_20px_rgba(16,185,129,0.15)] animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
                <CheckCircle2Icon className="h-5 w-5" />
              </span>
              <div className="flex flex-col items-start">
                <p className="text-sm font-semibold text-emerald-400">{successMessage}</p>
                <p className="text-[11px] text-emerald-500/70">Data successfully pushed to the pilot dashboard.</p>
              </div>
            </div>
          </div>
        )}
        <div className="flex gap-3">
          <button
            type="button"
            className="inline-flex items-center justify-center min-w-[140px] gap-2 rounded-lg border border-slate-700 bg-panel px-6 py-2.5 text-sm font-bold text-white transition-colors hover:bg-slate-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            <UploadIcon className="h-4 w-4" />
            Upload CSV
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving || blockTimer > 0}
            className="inline-flex items-center justify-center min-w-[200px] gap-2 rounded-lg bg-emerald-600 px-6 py-2.5 text-sm font-bold text-white transition-colors hover:bg-emerald-500 disabled:opacity-70 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
          >
            {saving ? 'Saving...' : blockTimer > 0 ? `Verify & Save (${blockTimer}s)` : 'Verify & Save Forecast'}
          </button>
        </div>
      </div>
    </form>
  );
}