import React from 'react';
import { ConstructionIcon } from 'lucide-react';

type PlaceholderPageProps = {
  title: string;
  description: string;
};

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight text-white">{title}</h1>
        <p className="mt-2 text-sm text-slate-400">{description}</p>
      </header>
      <section className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-line bg-panel px-6 py-20 text-center">
        <ConstructionIcon className="h-6 w-6 text-slate-500" aria-hidden="true" />
        <p className="text-sm font-semibold text-slate-200">Module in preparation</p>
        <p className="max-w-md text-xs text-slate-500">
          This workspace area is not part of the current console release. Observation and forecast data
          remain available from the Dashboard.
        </p>
      </section>
    </div>);

}