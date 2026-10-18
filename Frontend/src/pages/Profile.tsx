import React, { useState } from 'react';
import { CheckIcon, ShieldCheckIcon, AlertTriangleIcon } from 'lucide-react';
import { TextField } from '../components/auth/TextField';
import { useAuth } from '../contexts/AuthContext';
import { roleMeta } from '../types/auth';

export function Profile() {
  const { user, updateUser, deactivateAccount } = useAuth();
  const [form, setForm] = useState({
    name: user?.name ?? '',
    email: user?.email ?? '',
    phone: user?.phone ?? '',
    reference: user?.reference ?? '',
    organisation: user?.organisation ?? '',
    station: user?.station ?? ''
  });
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  if (!user) return null;

  const isPilot = user.role === 'pilot';
  const set = (key: keyof typeof form) => (value: string) => {
    setForm((previous) => ({ ...previous, [key]: value }));
    setSaved(false);
    setError('');
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await updateUser(form);
      setSaved(true);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to update profile.');
      setSaved(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent-soft">Your account</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">Profile</h1>
        <p className="mt-2 text-sm text-slate-400">
          Keep your operational contact details and credentials current.
        </p>
      </header>

      <section className="flex flex-col gap-5 rounded-xl border border-line bg-panel p-5 sm:flex-row sm:items-center sm:gap-6 sm:p-6">
        <span className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-accent-deep text-lg font-bold text-white">
          {user.initials}
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-lg font-bold text-white">{user.name}</h2>
          <p className="mt-1 text-sm text-slate-400">
            {user.title} · {user.organisation}
          </p>
          <p className="mt-3 inline-flex items-center gap-2 rounded-full border border-accent/50 bg-accent/10 px-3 py-1 text-[11px] font-semibold text-accent-pale">
            <ShieldCheckIcon className="h-3.5 w-3.5" aria-hidden="true" />
            {roleMeta[user.role].label} access
          </p>
        </div>
        <dl className="grid grid-cols-2 gap-4 sm:w-56">
          <div>
            <dt className="text-[10px] uppercase tracking-[0.15em] text-slate-500">Station</dt>
            <dd className="mt-1 text-sm font-semibold text-slate-100">VCBI</dd>
          </div>
          <div>
            <dt className="text-[10px] uppercase tracking-[0.15em] text-slate-500">Status</dt>
            <dd className="mt-1 text-sm font-semibold text-emerald-600 dark:text-emerald-300">Active</dd>
          </div>
        </dl>
      </section>

      <form onSubmit={handleSubmit} className="rounded-xl border border-line bg-panel p-5 sm:p-6">
        <h2 className="text-lg font-bold text-white">Personal details</h2>
        <p className="mt-1 text-xs text-slate-400">
          Changes apply to your session immediately and are shown across the console.
        </p>

        <div className="mt-6 grid gap-5 sm:grid-cols-2">
          <TextField id="profile-name" label="Full name" value={form.name} onChange={set('name')} />
          <div>
            <label htmlFor="profile-email" className="block text-xs font-semibold text-slate-400">
              Official email
            </label>
            <input
              id="profile-email"
              type="email"
              value={form.email}
              disabled
              className="mt-2 block w-full rounded-lg border border-line-strong bg-panel px-3 py-2 text-sm text-slate-500 opacity-70 cursor-not-allowed"
            />
            <p className="mt-1 text-[11px] text-slate-500">Contact IT support to change your official email address.</p>
          </div>
          
          <TextField id="profile-phone" label="Contact number" value={form.phone} onChange={set('phone')} />
          <TextField
            id="profile-reference"
            label={isPilot ? 'Licence number' : 'Met Officer ID'}
            value={form.reference}
            onChange={set('reference')} />
          
          <TextField
            id="profile-organisation"
            label={isPilot ? 'Airline / operator' : 'Organisation'}
            value={form.organisation}
            onChange={set('organisation')} />
          
          <TextField
            id="profile-station"
            label={isPilot ? 'Home base' : 'Duty station'}
            value={form.station}
            onChange={set('station')} />
          
        </div>

        {error && (
          <div className="mt-4 flex items-start gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-200" role="alert">
            <AlertTriangleIcon className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            {error}
          </div>
        )}

        {saved && !error && (
          <div className="mt-4 flex items-start gap-2 rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-700 dark:text-emerald-200" role="alert">
            <CheckIcon className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            Profile updated successfully!
          </div>
        )}

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <button
            type="submit"
            className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-bold text-white transition-colors hover:bg-sky-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-soft">
            
            Save changes
          </button>
        </div>
      </form>
    </div>);

}