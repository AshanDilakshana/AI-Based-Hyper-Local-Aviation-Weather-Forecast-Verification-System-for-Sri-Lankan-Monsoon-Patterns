import React from 'react';
import { motion } from 'framer-motion';
import type { Metric, MetricTone } from '../../types/weather';

const toneClasses: Record<MetricTone, { text: string; glow: string; dot: string }> = {
  amber: { text: 'text-amber-400', glow: 'group-hover:border-amber-500/40', dot: 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.5)]' },
  sky: { text: 'text-sky-400', glow: 'group-hover:border-sky-500/40', dot: 'bg-sky-400 shadow-[0_0_8px_rgba(56,189,248,0.5)]' },
  cyan: { text: 'text-cyan-400', glow: 'group-hover:border-cyan-500/40', dot: 'bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.5)]' },
  emerald: { text: 'text-emerald-400', glow: 'group-hover:border-emerald-500/40', dot: 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]' },
  slate: { text: 'text-slate-300', glow: 'group-hover:border-slate-400/40', dot: 'bg-slate-400 shadow-[0_0_8px_rgba(148,163,184,0.5)]' },
  green: { text: 'text-emerald-400', glow: 'group-hover:border-emerald-500/40', dot: 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]' }
};

export function MetricCard({ label, value, unit, footnote, tone }: Metric) {
  const currentTone = toneClasses[tone] || toneClasses.slate;

  return (
    <motion.article 
      whileHover={{ y: -3, transition: { duration: 0.2, ease: "easeOut" } }}
      className={`group relative overflow-hidden rounded-2xl border border-line/60 bg-panel/80 backdrop-blur-md p-4 sm:p-5 transition-all duration-300 hover:shadow-xl hover:shadow-accent/5 ${currentTone.glow}`}
    >
      {/* Top subtle highlight */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
      
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-xs font-bold tracking-wider uppercase text-slate-400 group-hover:text-slate-300 transition-colors">
          {label}
        </h3>
        <span className={`h-2 w-2 shrink-0 rounded-full ${currentTone.dot}`} />
      </div>

      <div className="mt-3 flex items-baseline justify-between gap-2 min-w-0">
        <span className="text-2xl sm:text-3xl font-black tracking-tight text-white tabular-nums drop-shadow-sm">
          {value}
        </span>
        {unit ? (
          <span className="text-xs sm:text-sm font-semibold text-slate-400 shrink-0 ml-1">
            {unit}
          </span>
        ) : null}
      </div>

      {footnote ? (
        <p className={`mt-2.5 text-xs font-semibold flex items-center gap-1.5 ${currentTone.text}`}>
          {footnote}
        </p>
      ) : null}
    </motion.article>
  );
}