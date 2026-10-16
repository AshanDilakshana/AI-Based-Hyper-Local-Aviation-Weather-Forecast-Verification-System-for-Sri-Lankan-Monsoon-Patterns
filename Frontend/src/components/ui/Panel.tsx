import React from 'react';
import { motion } from 'framer-motion';

type PanelProps = {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
};

export function Panel({ title, subtitle, action, children, className = '' }: PanelProps) {
  return (
    <motion.section 
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: "easeOut" }}
      className={`group relative overflow-hidden rounded-2xl border border-line/60 bg-panel/85 backdrop-blur-xl p-5 sm:p-6 shadow-xl shadow-black/20 transition-all duration-300 hover:border-line ${className}`}
    >
      {/* Top subtle glow line */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-accent/30 to-transparent opacity-60" />

      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-white flex items-center gap-2.5">
            <span className="h-2 w-2 rounded-full bg-accent shadow-[0_0_8px_rgba(234,179,8,0.6)]" />
            {title}
          </h2>
          {subtitle ? <p className="mt-1.5 text-xs text-slate-400 font-medium">{subtitle}</p> : null}
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
      <div className="mt-6">{children}</div>
    </motion.section>
  );
}