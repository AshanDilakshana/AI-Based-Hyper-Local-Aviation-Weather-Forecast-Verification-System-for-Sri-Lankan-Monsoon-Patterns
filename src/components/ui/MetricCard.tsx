import React from 'react';
import type { Metric, MetricTone } from '../../types/weather';

const toneClasses: Record<MetricTone, string> = {
  amber: 'text-amber-600 dark:text-amber-300',
  sky: 'text-accent-pale',
  cyan: 'text-cyan-700 dark:text-cyan-300',
  emerald: 'text-emerald-600 dark:text-emerald-300',
  slate: 'text-slate-100',
  green: 'text-emerald-600 dark:text-emerald-400'
};

export function MetricCard({ label, value, unit, footnote, tone }: Metric) {
  return (
    <article className="rounded-xl border border-line bg-panel p-4">
      <h3 className="text-xs text-slate-400">{label}</h3>
      <p className="mt-2 flex items-baseline gap-1.5">
        <span className="text-2xl font-bold leading-8 text-white">{value}</span>
        {unit ? <span className="text-xs text-slate-500">{unit}</span> : null}
      </p>
      <p className={`mt-3 text-xs ${toneClasses[tone]}`}>{footnote}</p>
    </article>);

}