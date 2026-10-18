import React from 'react';

interface PageHeadingProps {
  eyebrow: string;
  title: string;
  description: string;
  aside?: React.ReactNode;
}

export function PageHeading({ eyebrow, title, description, aside }: PageHeadingProps) {
  return (
    <div className="flex flex-col gap-4 border-b border-line pb-6 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-bright">{eyebrow}</p>
        <h1 className="mt-1 text-3xl font-bold -tracking-[0.02em] text-white">{title}</h1>
        <p className="mt-1 text-sm text-subtle">{description}</p>
      </div>
      {aside}
    </div>);

}

export function LiveFeedBadge() {
  return (
    <div className="inline-flex items-center gap-2 rounded-lg border border-line bg-inset px-4 py-2.5">
      <span className="h-2 w-2 rounded-full bg-ok" aria-hidden="true" />
      <span className="text-xs text-subtle">Live station feed:</span>
      <span className="text-xs font-bold text-bright">VCBI 08:30 SLST</span>
    </div>);

}