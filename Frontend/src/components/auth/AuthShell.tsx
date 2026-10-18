import React from 'react';
import { PlaneTakeoffIcon } from 'lucide-react';
import { STATION } from '../../data/weather';
import { ThemeToggle } from '../ui/ThemeToggle';

type AuthShellProps = {
  eyebrow: string;
  title: string;
  description: string;
  children: React.ReactNode;
  footer: React.ReactNode;
};

export function AuthShell({ eyebrow, title, description, children, footer }: AuthShellProps) {
  return (
    <div className="flex min-h-screen w-full bg-canvas font-sans text-slate-200">
      <aside className="relative hidden w-[46%] shrink-0 overflow-hidden border-r border-line lg:block">
        <img
          src="/3493b474-3756-40f5-bc97-04fdf96ad765.jpg"
          alt="Bandaranaike International Airport control tower at dusk"
          className="absolute inset-0 h-full w-full object-cover opacity-70" />
        
        <div className="absolute inset-0 bg-rail/80" aria-hidden="true" />
        <div className="relative flex h-full flex-col justify-between p-10">
          <div className="flex flex-col items-start gap-1">
            <div className="flex items-center justify-center rounded-2xl border border-line/70 bg-panel/40 p-3.5 backdrop-blur-md shadow-lg shadow-black/10 transition-all hover:border-line">
              {/* Logo with dark and light mode dynamic source */}
              <img 
                src="/bia_logo_transparent.png" 
                alt="BIA Logo" 
                className="h-24 w-auto object-contain dark:hidden drop-shadow-sm" 
              />
              <img 
                src="/bia_logo_dark.png" 
                alt="BIA Logo" 
                className="h-24 w-auto object-contain hidden dark:block drop-shadow-[0_2px_12px_rgba(56,189,248,0.2)]" 
              />
            </div>
            <span className="flex flex-col mt-2">
              <span className="text-xs font-semibold uppercase tracking-[0.2em] text-accent-pale">
                Sri Lanka
              </span>
              <span className="text-2xl font-black tracking-wide text-white drop-shadow-sm">MET AVIATION</span>
            </span>
          </div>

          <div className="max-w-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent-soft">
              {STATION.fir}
            </p>
            <h2 className="mt-3 text-2xl font-bold leading-snug text-white">
              Aerodrome weather intelligence for {STATION.codes}
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-400">
              {STATION.airport}. Observations, hyper-local model runs and aviation charts in one console.
            </p>
          </div>

          <dl className="grid grid-cols-3 gap-4 border-t border-line/80 pt-6">
            <div>
              <dt className="text-[10px] uppercase tracking-[0.15em] text-slate-500">Station</dt>
              <dd className="mt-1 text-sm font-semibold text-slate-100">VCBI</dd>
            </div>
            <div>
              <dt className="text-[10px] uppercase tracking-[0.15em] text-slate-500">Stream</dt>
              <dd className="mt-1 text-sm font-semibold text-emerald-600 dark:text-emerald-300">Live</dd>
            </div>
            <div>
              <dt className="text-[10px] uppercase tracking-[0.15em] text-slate-500">Cycle</dt>
              <dd className="mt-1 text-sm font-semibold text-slate-100">15 min</dd>
            </div>
          </dl>
        </div>
      </aside>

      <main className="relative flex w-full flex-1 items-center justify-center px-4 py-12 sm:px-8">
        <div className="absolute right-4 top-6 sm:right-8">
          <ThemeToggle />
        </div>
        <div className="w-full max-w-md">
          {/* Logo on small screens where aside is hidden */}
          <div className="mb-6 flex items-center gap-3 lg:hidden">
            <div className="flex items-center justify-center rounded-xl border border-line/70 bg-panel/50 p-2 backdrop-blur-md shadow-sm">
              <img 
                src="/bia_logo_transparent.png" 
                alt="BIA Logo" 
                className="h-12 w-auto object-contain dark:hidden" 
              />
              <img 
                src="/bia_logo_dark.png" 
                alt="BIA Logo" 
                className="h-12 w-auto object-contain hidden dark:block" 
              />
            </div>
            <div>
              <span className="block text-[10px] font-bold uppercase tracking-[0.2em] text-accent-soft">Sri Lanka</span>
              <span className="block text-lg font-black tracking-wide text-white">MET AVIATION</span>
            </div>
          </div>

          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent-soft">{eyebrow}</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">{title}</h1>
          <p className="mt-2 text-sm text-slate-400">{description}</p>
          <div className="mt-8">{children}</div>
          <div className="mt-6 text-sm text-slate-400">{footer}</div>
        </div>
      </main>
    </div>);

}