import React from 'react';
import { ArrowRightIcon, ClockIcon, MapPinIcon, PlaneIcon, PlaneTakeoffIcon } from 'lucide-react';
import type { FlightStat } from '../../types/aviation';

const icons = {
  route: PlaneTakeoffIcon,
  duration: ClockIcon,
  distance: ArrowRightIcon,
  aircraft: PlaneIcon,
  terminal: MapPinIcon
};

export function StatCard({ label, value, icon }: FlightStat) {
  const Icon = icons[icon];

  return (
    <div className="rounded-lg border border-line bg-panel p-4">
      <p className="flex items-center gap-2 text-[11px] font-medium tracking-wide text-muted">
        <Icon className="h-5 w-5 text-sky-bright" aria-hidden="true" />
        {label}
      </p>
      <p className="mt-2 text-lg font-bold text-white">{value}</p>
    </div>);

}