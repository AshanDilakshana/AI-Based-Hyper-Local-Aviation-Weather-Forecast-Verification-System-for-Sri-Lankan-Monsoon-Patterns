import React, { useMemo, useState } from 'react';
import { DownloadIcon, ExternalLinkIcon } from 'lucide-react';

const flightLevels = ['FL050', 'FL100', 'FL180', 'FL240', 'FL300', 'FL340', 'FL390', 'FL450'];

const chartAreas = [
{ label: 'Area A (North America)', code: 'a' },
{ label: 'Area B (Pacific)', code: 'b' },
{ label: 'Area C (Europe-Africa)', code: 'c' },
{ label: 'Area D (Asia)', code: 'd' },
{ label: 'Area E (Australasia)', code: 'e' },
{ label: 'Area F (South America)', code: 'f' }];


const leadTimes = [
{ label: '+06 Hours (F06)', code: 'F06' },
{ label: '+12 Hours (F12)', code: 'F12' },
{ label: '+18 Hours (F18)', code: 'F18' },
{ label: '+24 Hours (F24)', code: 'F24' }];


const CHART_IMAGE = "/6c166cdf-470c-4145-8af4-d4301d0c11c6.jpg";


const selectClass =
'h-10 w-full rounded-lg border border-line-strong bg-inset px-3 pr-8 text-sm font-medium text-slate-100 outline-none transition-colors focus:border-accent';

export function RouteMaps() {
  const [level, setLevel] = useState('FL340');
  const [area, setArea] = useState(chartAreas[2].label);
  const [lead, setLead] = useState(leadTimes[0].label);

  const fileName = useMemo(() => {
    const areaCode = chartAreas.find((item) => item.label === area)?.code ?? 'c';
    const leadCode = leadTimes.find((item) => item.label === lead)?.code ?? 'F06';
    return `${leadCode}_wind_${level.replace('FL', '')}_${areaCode}.gif`;
  }, [area, lead, level]);

  return (
    <div className="w-full">
      <header className="flex flex-col gap-5 border-b border-line pb-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Aviation Forecast Maps Explorer</h1>
          <p className="mt-1 text-sm text-slate-500">
            Select parameters to download Wind &amp; Temp Aloft charts directly from NOAA AWC
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-3 xl:w-[600px]">
          <div>
            <label
              htmlFor="chart-level"
              className="block text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
              
              Flight level
            </label>
            <select
              id="chart-level"
              value={level}
              onChange={(event) => setLevel(event.target.value)}
              className={`${selectClass} mt-1.5`}>
              
              {flightLevels.map((option) =>
              <option key={option}>{option}</option>
              )}
            </select>
          </div>
          <div>
            <label
              htmlFor="chart-area"
              className="block text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
              
              Fax chart area
            </label>
            <select
              id="chart-area"
              value={area}
              onChange={(event) => setArea(event.target.value)}
              className={`${selectClass} mt-1.5`}>
              
              {chartAreas.map((option) =>
              <option key={option.code}>{option.label}</option>
              )}
            </select>
          </div>
          <div>
            <label
              htmlFor="chart-lead"
              className="block text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
              
              Forecast lead time
            </label>
            <select
              id="chart-lead"
              value={lead}
              onChange={(event) => setLead(event.target.value)}
              className={`${selectClass} mt-1.5`}>
              
              {leadTimes.map((option) =>
              <option key={option.code}>{option.label}</option>
              )}
            </select>
          </div>
        </div>
      </header>

      <section className="mt-6 rounded-xl border border-line bg-panel p-5 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-slate-400">
            Aviation Chart: <span className="font-bold text-slate-100">{fileName}</span>
          </p>
          <div className="flex items-center gap-4">
            <p className="text-sm text-slate-400">
              Target Server: <span className="font-bold text-slate-100">aviationweather.gov</span>
            </p>
            <a
              href={CHART_IMAGE}
              download={fileName}
              className="inline-flex items-center gap-2 rounded-lg bg-accent px-3 py-2 text-xs font-bold text-white transition-colors hover:bg-sky-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-soft">
              
              <DownloadIcon className="h-4 w-4" aria-hidden="true" />
              Download
            </a>
          </div>
        </div>

        <figure className="mt-6 flex justify-center">
          <img
            src={CHART_IMAGE}
            alt={`Wind and temperature aloft fax chart ${fileName} for ${area} at ${level}, valid ${lead}`}
            className="w-full max-w-[540px] border border-line-strong bg-[#FFFFFF] object-contain" />
          
        </figure>

        <figcaption className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
          <span>
            {area} · {level} · {lead} · WAFC Washington
          </span>
          <a
            href="https://aviationweather.gov"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 font-semibold text-accent-pale hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-accent">
            
            Open source archive
            <ExternalLinkIcon className="h-3.5 w-3.5" aria-hidden="true" />
          </a>
        </figcaption>
      </section>
    </div>);

}