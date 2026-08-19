import React, { useState } from 'react';
import { MapPinIcon, MinusIcon, PlusIcon } from 'lucide-react';
import { SegmentedControl } from '../ui/SegmentedControl';

const layers = ['Wind vectors', 'Temperature', 'Pressure', 'Rain probability'];

export function ForecastMap() {
  const [horizon, setHorizon] = useState('+1 Hour');
  const [layer, setLayer] = useState('Temperature');
  const [zoom, setZoom] = useState(1);

  return (
    <section className="rounded-xl border border-line bg-panel p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">Weather forecast map</h2>
          <p className="mt-1 text-xs text-slate-400">Colombo airport observation grid</p>
        </div>
        <SegmentedControl
          label="Forecast horizon"
          options={['+1 Hour', '+2 Hours', '+3 Hours']}
          value={horizon}
          onChange={setHorizon} />
        
      </div>

      <div className="relative mt-6 h-96 lg:h-[450px] xl:h-[520px] overflow-hidden rounded-lg border border-line-strong bg-inset">
        <img
          src="/88c88d57-eaef-4bab-a144-3dee218172d4.jpg"
          alt={`${layer} field forecast for ${horizon} over the Colombo airport grid`}
          className="h-full w-full object-cover transition-transform duration-300"
          style={{ transform: `scale(${zoom})` }} />
        

        <span
          className="absolute left-1/2 top-1/2 flex h-12 w-12 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border-2 border-[#FFFFFF] bg-accent shadow-lg"
          aria-hidden="true">
          
          <MapPinIcon className="h-5 w-5 text-white" />
        </span>

        <div className="absolute bottom-4 left-4 rounded border border-line-strong bg-ink/95 px-3 py-2">
          <p className="text-xs font-semibold text-white">VCBI</p>
          <p className="text-xs text-slate-400">29.2°C · 14 kt WSW</p>
        </div>

        <div className="absolute right-3 top-3 flex flex-col overflow-hidden rounded border border-line-strong bg-ink/90">
          <button
            type="button"
            onClick={() => setZoom((z) => Math.min(2, +(z + 0.2).toFixed(1)))}
            className="px-3 py-1.5 text-lg leading-6 text-white transition-colors hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            aria-label="Zoom in">
            
            <PlusIcon className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={() => setZoom((z) => Math.max(1, +(z - 0.2).toFixed(1)))}
            className="border-t border-line-strong px-3 py-1.5 text-lg leading-6 text-white transition-colors hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            aria-label="Zoom out">
            
            <MinusIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap gap-2" role="group" aria-label="Map layer">
        {layers.map((item) => {
          const isActive = item === layer;
          return (
            <button
              key={item}
              type="button"
              onClick={() => setLayer(item)}
              aria-pressed={isActive}
              className={`rounded-full border px-3.5 py-1.5 text-xs transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
              isActive ?
              'border-accent-soft bg-accent text-accent-ice' :
              'border-line-strong text-slate-400 hover:text-slate-200'}`
              }>
              
              {item}
            </button>);

        })}
      </div>
    </section>);

}