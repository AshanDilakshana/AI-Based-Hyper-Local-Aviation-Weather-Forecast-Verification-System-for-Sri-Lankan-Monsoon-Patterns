import React from 'react';
import { CloudIcon, EyeIcon, ThermometerIcon, WindIcon } from 'lucide-react';
import type { WeatherMetric } from '../../types/aviation';

const icons = {
  wind: WindIcon,
  visibility: EyeIcon,
  temperature: ThermometerIcon,
  cloud: CloudIcon
};

export function MetricTile({ label, value, detail, icon }: WeatherMetric) {
  const Icon = icons[icon];

  return (
    <div className="rounded-lg border border-lineStrong bg-panelDeep/60 p-3">
      <p className="flex items-center gap-2 text-xs text-subtle">
        <Icon className="h-[13px] w-[13px]" aria-hidden="true" />
        {label}
      </p>
      <p className="mt-1 text-lg font-semibold text-white">{value}</p>
      <p className="text-[11px] text-muted">{detail}</p>
    </div>);

}