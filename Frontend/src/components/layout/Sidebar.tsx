import React, { useEffect, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  ActivityIcon,
  CloudSunIcon,
  FileTextIcon,
  LayoutDashboardIcon,
  LogOutIcon,
  MapIcon,
  PlaneTakeoffIcon,
  SettingsIcon,
  UserIcon,
  XIcon,
  ClockIcon
} from
'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { roleMeta } from '../../types/auth';

type SidebarProps = {
  open: boolean;
  onClose: () => void;
};

const forecasterNav = [
{ to: '/', label: 'Dashboard', Icon: LayoutDashboardIcon, end: true },
{ to: '/forecasting', label: 'Weather Forecasting', Icon: CloudSunIcon, end: false },
{ to: '/maps', label: 'Forecast Maps', Icon: MapIcon, end: false },
{ to: '/logs', label: 'Activity Logs', Icon: ActivityIcon, end: false }];


const pilotNav = [
{ to: '/pilot', label: 'Dashboard', Icon: LayoutDashboardIcon, end: true },
{ to: '/pilot/flight-planning', label: 'Flight Planning', Icon: PlaneTakeoffIcon, end: false },
{ to: '/pilot/briefing', label: 'Weather Briefing', Icon: CloudSunIcon, end: false },
{ to: '/pilot/maps', label: 'Forecast Maps', Icon: MapIcon, end: false },
{ to: '/pilot/documents', label: 'My Documents', Icon: FileTextIcon, end: false },
{ to: '/pilot/recent-plans', label: 'Recent Flight Plans', Icon: ClockIcon, end: false },
{ to: '/logs', label: 'Activity Logs', Icon: ActivityIcon, end: false }];


const linkClass = ({ isActive }: {isActive: boolean;}) =>
`flex items-center gap-3 rounded-lg px-3 py-3 text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
isActive ?
'bg-accent text-white shadow-lg shadow-sky-950/20' :
'text-slate-400 hover:bg-slate-500/10 hover:text-slate-100'}`;


export function Sidebar({ open, onClose }: SidebarProps) {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const visibleItems = user?.role === 'pilot' ? pilotNav : forecasterNav;

  const handleSignOut = () => {
    onClose();
    signOut();
    navigate('/sign-in', { replace: true });
  };

  return (
    <>
      <div
        className={`fixed inset-0 z-30 bg-slate-900/60 lg:hidden ${open ? 'block' : 'hidden'}`}
        onClick={onClose}
        aria-hidden="true" />
      
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col overflow-y-auto border-r border-line bg-rail transition-transform duration-200 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 ${
        open ? 'translate-x-0' : '-translate-x-full'}`
        }
        aria-label="Primary">
        
        <div className="flex items-center justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg border border-accent-soft bg-accent text-white">
              <PlaneTakeoffIcon className="h-5 w-5" aria-hidden="true" />
            </span>
            <span className="flex flex-col">
              <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-accent-pale">
                Sri Lanka
              </span>
              <span className="text-sm font-bold tracking-wide text-white">MET AVIATION</span>
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-slate-400 transition-colors hover:text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent lg:hidden"
            aria-label="Close navigation">
            
            <XIcon className="h-5 w-5" />
          </button>
        </div>

        <div className="px-6 pb-2 pt-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
            Operations workspace
          </p>
          <p className="mt-1 text-sm font-medium text-slate-200">
            {user ? `${roleMeta[user.role].label} console` : 'Meteorological console'}
          </p>
        </div>

        <nav className="flex flex-1 flex-col gap-1 px-6 py-4">
          {visibleItems.map(({ to, label, Icon, end }) =>
          <NavLink key={to} to={to} end={end} onClick={onClose} className={linkClass}>
              <Icon className="h-[18px] w-[18px]" aria-hidden="true" />
              {label}
            </NavLink>
          )}
        </nav>

        <div className="mx-6 mb-6 border-t border-line pt-4">
          <NavLink to="/profile" onClick={onClose} className={linkClass}>
            <UserIcon className="h-[18px] w-[18px]" aria-hidden="true" />
            Profile
          </NavLink>
          <NavLink to="/settings" onClick={onClose} className={linkClass}>
            <SettingsIcon className="h-[18px] w-[18px]" aria-hidden="true" />
            Settings
          </NavLink>
          <button
            type="button"
            onClick={handleSignOut}
            className="mt-1 flex w-full items-center gap-3 rounded-lg px-3 py-3 text-sm text-slate-400 transition-colors hover:bg-rose-500/10 hover:text-rose-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent">
            
            <LogOutIcon className="h-[18px] w-[18px]" aria-hidden="true" />
            {user ? 'Log out' : 'Sign in'}
          </button>

          <div className="mt-4 rounded-lg border border-emerald-500/40 bg-emerald-500/10 p-3">
            <p className="flex items-center gap-2 text-xs font-semibold text-emerald-600 dark:text-emerald-300">
              <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
              System operational
            </p>
            <p className="mt-2 text-[11px] leading-relaxed text-slate-500">
              VCBI Met data stream updated 2 min ago
            </p>
          </div>
        </div>
      </aside>
    </>);

}