import React from 'react';
import { PlaneIcon } from 'lucide-react';

interface Endpoint {
  code: string;
  city: string;
}

interface RouteDiagramProps {
  origin: Endpoint;
  destination: Endpoint;
  caption: string;
}

function Node() {
  return (
    <span className="flex h-6 w-6 items-center justify-center rounded-full border-4 border-sky-bright bg-sky-pale">
      <span className="h-2 w-2 rounded-full bg-sky-deep" aria-hidden="true" />
    </span>);

}

export function RouteDiagram({ origin, destination, caption }: RouteDiagramProps) {
  return (
    <div className="rounded-lg border border-lineStrong bg-panelDeep p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Node />
          <p className="mt-3 text-sm font-bold text-white">{origin.code}</p>
          <p className="text-xs text-subtle">{origin.city}</p>
        </div>

        <div className="relative mt-3 flex-1" aria-hidden="true">
          <div className="h-px w-full bg-sky-bright/70" />
          <PlaneIcon className="absolute top-1/2 h-5 w-5 -translate-x-1/2 -translate-y-1/2 rotate-45 text-sky-bright animate-flight fill-sky-bright/20" />
        </div>

        <div className="text-right">
          <span className="flex justify-end">
            <Node />
          </span>
          <p className="mt-3 text-sm font-bold text-white">{destination.code}</p>
          <p className="text-xs text-subtle">{destination.city}</p>
        </div>
      </div>
      <p className="mt-8 text-[10px] uppercase tracking-[0.1em] text-muted">{caption}</p>
    </div>);

}