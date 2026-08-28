import React, { useState } from 'react';
import { MapPinIcon, MinusIcon, PlusIcon } from 'lucide-react';
import { SegmentedControl } from '../ui/SegmentedControl';

const layers = ['Wind vectors', 'Temperature', 'Pressure', 'Rain probability'];

export function ForecastMap() {
  const [layer, setLayer] = useState('Temperature');
  const [zoom, setZoom] = useState(1);

  return (
    <section className="rounded-xl border border-line bg-panel p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">Live trend monitor</h2>
          <p className="mt-1 text-xs text-slate-400">Colombo airport observation grid</p>
        </div>
      </div>

      <div className="relative mt-6 h-96 lg:h-[450px] xl:h-[520px] overflow-hidden rounded-lg border border-line-strong bg-inset">
        <iframe
          src={`https://embed.windy.com/embed2.html?lat=7.18&lon=79.88&zoom=8&level=surface&overlay=${
            layer === 'Wind vectors' ? 'wind' : 
            layer === 'Pressure' ? 'pressure' : 
            layer === 'Rain probability' ? 'rain' : 'temp'
          }&menu=&message=&marker=true&calendar=&pressure=&type=map&location=coordinates&detail=&detailLat=7.18&detailLon=79.88&metricWind=kt&metricTemp=%C2%B0C&radarRange=-1`}
          className="absolute inset-0 h-full w-full border-0"
          title="Interactive Weather Forecast Map"
          allowFullScreen
        ></iframe>

        <div className="absolute bottom-4 left-4 rounded border border-line-strong bg-ink/95 px-3 py-2 pointer-events-none">
          <p className="text-xs font-semibold text-white">VCBI</p>
          <p className="text-xs text-slate-400">29.2°C · 14 kt WSW</p>
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