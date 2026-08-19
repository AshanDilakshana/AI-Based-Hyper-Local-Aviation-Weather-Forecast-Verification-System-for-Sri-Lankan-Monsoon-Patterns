import React from 'react';
import type { BriefingStatus } from '../../types/aviation';

const styles: Record<BriefingStatus, string> = {
  Draft: 'border-muted/60 bg-slate-500/20 text-faint',
  Approved: 'border-emerald-500/40 bg-emerald-500/15 text-emerald-700 dark:text-emerald-300',
  Pending: 'border-amber-400/50 bg-amber-400/15 text-amber-700 dark:text-amber-300'
};

export function StatusPill({ status }: {status: BriefingStatus;}) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-semibold ${styles[status]}`}>
      
      {status}
    </span>);

}