import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MenuIcon, RadioTowerIcon, ShieldCheckIcon, UserIcon } from 'lucide-react';
import { STATION } from '../../data/weather';
import { useAuth } from '../../contexts/AuthContext';
import { ThemeToggle } from '../ui/ThemeToggle';

type TopBarProps = {
  onMenuClick: () => void;
};

export function TopBar({ onMenuClick }: TopBarProps) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const slstTime = 'SLST ' + time.toLocaleTimeString('en-US', { timeZone: 'Asia/Colombo', hour12: false });
  const utcTime = 'UTC ' + time.toLocaleTimeString('en-US', { timeZone: 'UTC', hour12: false });

  return (
    <header className="sticky top-0 z-20 flex h-[74px] w-full items-center justify-between gap-4 border-b border-line/60 bg-topbar/80 backdrop-blur-xl px-4 sm:px-6 shadow-sm">
      <div className="flex min-w-0 items-center gap-4">
        <button
          type="button"
          onClick={onMenuClick}
          className="rounded-lg p-2 text-slate-300 transition-colors hover:bg-slate-500/10 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-accent lg:hidden"
          aria-label="Open navigation">
          <MenuIcon className="h-5 w-5" />
        </button>
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-xs font-bold tracking-[0.15em] text-accent-pale">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400"></span>
            </span>
            <RadioTowerIcon className="h-4 w-4 shrink-0 text-accent" aria-hidden="true" />
            <span className="truncate">{STATION.fir}</span>
          </p>
          <p className="mt-1 truncate text-xs text-slate-400 font-medium">
            {STATION.airport} <span className="font-bold text-white">{STATION.codes}</span>
          </p>
        </div>
      </div>

      <div className="hidden md:flex items-center gap-3 text-xs font-mono text-slate-300 px-4 py-2 rounded-xl border border-line/70 bg-panel/60 backdrop-blur-md shadow-sm">
        <span className="font-bold text-accent tracking-wider">{slstTime}</span>
        <span className="text-slate-600 font-normal">|</span>
        <span className="font-medium text-slate-300 tracking-wider">{utcTime}</span>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <ThemeToggle />

        {user ?
          <>

            <button
              type="button"
              onClick={() => navigate('/profile')}
              className="flex items-center gap-3 rounded-lg border border-transparent px-2 py-1 transition-colors hover:border-line focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
              aria-label="Open your profile">

              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-deep text-xs font-bold text-white">
                {user.initials}
              </span>
              <span className="hidden text-left sm:block">
                <span className="block text-xs font-semibold text-slate-100">{user.name}</span>
                <span className="block text-[10px] text-slate-500">
                  {user.title}
                  {user.reference ? ` · ${user.reference}` : ''}
                </span>
              </span>
            </button>

            <ShieldCheckIcon className="hidden h-[18px] w-[18px] text-emerald-500 sm:block" aria-hidden="true" />
          </> :

          <Link
            to="/sign-in"
            className="flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-xs font-semibold text-slate-300 transition-colors hover:border-accent hover:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent">

            <UserIcon className="h-[18px] w-[18px]" aria-hidden="true" />
            <span className="hidden sm:inline">Sign in</span>
          </Link>
        }
      </div>
    </header>);

}