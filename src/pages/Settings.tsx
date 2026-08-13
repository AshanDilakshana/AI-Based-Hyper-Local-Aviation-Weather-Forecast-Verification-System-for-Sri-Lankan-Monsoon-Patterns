import React, { useState } from 'react';
import { CheckIcon, MoonIcon, SunIcon } from 'lucide-react';
import { Switch } from '../components/ui/Switch';
import { ThemeToggle } from '../components/ui/ThemeToggle';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';

export function Settings() {
  const { theme, setTheme } = useTheme();
  const { user } = useAuth();
  const isPilot = user?.role === 'pilot';

  const [units, setUnits] = useState({ temperature: '°C', wind: 'kt', pressure: 'hPa' });
  const [refresh, setRefresh] = useState('15 min');
  const [alerts, setAlerts] = useState({
    thresholds: true,
    briefingApproval: true,
    dataOutage: true,
    digest: false
  });
  const [saved, setSaved] = useState(false);

  const markDirty = () => setSaved(false);

  return (
    <div className="flex flex-col gap-6">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent-soft">Preferences</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">Settings</h1>
        <p className="mt-2 text-sm text-slate-400">
          Appearance, measurement units, data refresh cadence and alerting for this console.
        </p>
      </header>

      <section className="rounded-xl border border-line bg-panel p-5 sm:p-6">
        <h2 className="text-lg font-bold text-white">Appearance</h2>
        <p className="mt-1 text-xs text-slate-400">
          Night mode is optimised for the operations room; day mode for briefing and printing.
        </p>

        <div className="mt-5 flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="grid flex-1 gap-3 sm:grid-cols-2">
            {(
            [
            { value: 'dark', label: 'Night mode', Icon: MoonIcon, hint: 'Low-glare console' },
            { value: 'light', label: 'Day mode', Icon: SunIcon, hint: 'High-contrast briefing' }] as
            const).
            map(({ value, label, Icon, hint }) => {
              const isActive = theme === value;
              return (
                <button
                  key={value}
                  type="button"
                  onClick={() => setTheme(value)}
                  aria-pressed={isActive}
                  className={`rounded-lg border p-4 text-left transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                  isActive ? 'border-accent bg-accent/10' : 'border-line-strong hover:border-accent/60'}`
                  }>
                  
                  <span className="flex items-center gap-2">
                    <Icon
                      className={`h-4 w-4 ${isActive ? 'text-accent-soft' : 'text-slate-500'}`}
                      aria-hidden="true" />
                    
                    <span className="text-sm font-semibold text-slate-100">{label}</span>
                  </span>
                  <span className="mt-1 block text-xs text-slate-500">{hint}</span>
                </button>);

            })}
          </div>
          <div className="flex items-center gap-3 sm:pl-6">
            <span className="text-xs text-slate-500">Quick switch</span>
            <ThemeToggle />
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-line bg-panel p-5 sm:p-6">
        <h2 className="text-lg font-bold text-white">Measurement units</h2>
        <p className="mt-1 text-xs text-slate-400">Applies to observation tables, tiles and briefings.</p>

        <div className="mt-5 grid gap-5 sm:grid-cols-3">
          <div>
            <p className="text-xs text-slate-400">Temperature</p>
            <div className="mt-2">
              <SegmentedControl
                label="Temperature unit"
                options={['°C', '°F']}
                value={units.temperature}
                onChange={(value) => {
                  setUnits((previous) => ({ ...previous, temperature: value }));
                  markDirty();
                }} />
              
            </div>
          </div>
          <div>
            <p className="text-xs text-slate-400">Wind speed</p>
            <div className="mt-2">
              <SegmentedControl
                label="Wind speed unit"
                options={['kt', 'm/s']}
                value={units.wind}
                onChange={(value) => {
                  setUnits((previous) => ({ ...previous, wind: value }));
                  markDirty();
                }} />
              
            </div>
          </div>
          <div>
            <p className="text-xs text-slate-400">Pressure</p>
            <div className="mt-2">
              <SegmentedControl
                label="Pressure unit"
                options={['hPa', 'inHg']}
                value={units.pressure}
                onChange={(value) => {
                  setUnits((previous) => ({ ...previous, pressure: value }));
                  markDirty();
                }} />
              
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-line bg-panel p-5 sm:p-6">
        <h2 className="text-lg font-bold text-white">Data &amp; alerts</h2>
        <p className="mt-1 text-xs text-slate-400">
          Control how often the station feed is polled and what you get notified about.
        </p>

        <div className="mt-5">
          <p className="text-xs text-slate-400">Observation refresh interval</p>
          <div className="mt-2">
            <SegmentedControl
              label="Refresh interval"
              options={['5 min', '15 min', '30 min']}
              value={refresh}
              onChange={(value) => {
                setRefresh(value);
                markDirty();
              }} />
            
          </div>
        </div>

        <div className="mt-5 divide-y divide-line border-t border-line">
          <Switch
            label="Threshold alerts"
            description="Crosswind above 15 kt, visibility below 5 km, or cloud base under 1,000 ft."
            checked={alerts.thresholds}
            onChange={(checked) => {
              setAlerts((previous) => ({ ...previous, thresholds: checked }));
              markDirty();
            }} />
          
          <Switch
            label={isPilot ? 'Briefing approval updates' : 'Briefing requests from crew'}
            description={
            isPilot ?
            'Notify me when the Met desk approves or rejects a briefing.' :
            'Notify me when flight crew submit a briefing request for review.'
            }
            checked={alerts.briefingApproval}
            onChange={(checked) => {
              setAlerts((previous) => ({ ...previous, briefingApproval: checked }));
              markDirty();
            }} />
          
          <Switch
            label="Data stream outage"
            description="Alert if the VCBI automatic station stops reporting."
            checked={alerts.dataOutage}
            onChange={(checked) => {
              setAlerts((previous) => ({ ...previous, dataOutage: checked }));
              markDirty();
            }} />
          
          <Switch
            label="Daily email digest"
            description="A 06:00 SLST summary of the previous operational day."
            checked={alerts.digest}
            onChange={(checked) => {
              setAlerts((previous) => ({ ...previous, digest: checked }));
              markDirty();
            }} />
          
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => setSaved(true)}
            className="rounded-lg bg-accent px-4 py-2.5 text-sm font-bold text-white transition-colors hover:bg-sky-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-soft">
            
            Save preferences
          </button>
          {saved ?
          <p
            className="inline-flex items-center gap-2 text-xs font-semibold text-emerald-600 dark:text-emerald-300"
            role="status">
            
              <CheckIcon className="h-4 w-4" aria-hidden="true" />
              Preferences saved
            </p> :
          null}
        </div>
      </section>
    </div>);

}