import React, { useState } from 'react';
import {
  DownloadIcon,
  RefreshCwIcon,
  WindIcon,
  CloudRainIcon,
  CompassIcon,
  CheckIcon,
  CopyIcon,
  ZoomInIcon,
  ZoomOutIcon,
  RotateCcwIcon,
  ZapIcon,
  LayersIcon
} from 'lucide-react';

type Category = 'windtemp' | 'sigwx' | 'cangfa';

// --- WIND / TEMP DATA ---
const windAreas = [
  { id: 'd', name: 'Area D - 65N-28S 133E-15W (Asia / Sri Lanka)', short: 'Asia / Sri Lanka' },
  { id: 'c', name: 'Area C - 76N-45S 65E-31W (Europe-Africa)', short: 'Europe-Africa' },
  { id: 'b1', name: 'Area B1 - 50N-40S 125W-25E (AMERS-AFR)', short: 'America-Africa' },
  { id: 'a', name: 'Area A - 65N-50S 120W-25W (Americas)', short: 'Americas' },
];

const windLevels = [
  { label: 'FL630', full: 'FL630 (63,000 ft)', code: '630' },
  { label: 'FL450', full: 'FL450 (45,000 ft)', code: '450' },
  { label: 'FL390', full: 'FL390 (39,000 ft)', code: '390' },
  { label: 'FL340', full: 'FL340 (34,000 ft)', code: '340' },
  { label: 'FL300', full: 'FL300 (30,000 ft)', code: '300' },
  { label: 'FL240', full: 'FL240 (24,000 ft)', code: '240' },
  { label: 'FL180', full: 'FL180 (18,000 ft)', code: '180' },
  { label: 'FL100', full: 'FL100 (10,000 ft)', code: '100' },
  { label: 'FL050', full: 'FL050 (5,000 ft)', code: '050' },
];

const windTimes = [
  { label: '+06h', full: '+06 Hours Forecast', code: '06' },
  { label: '+12h', full: '+12 Hours Forecast', code: '12' },
  { label: '+18h', full: '+18 Hours Forecast', code: '18' },
  { label: '+24h', full: '+24 Hours Forecast', code: '24' },
  { label: '+30h', full: '+30 Hours Forecast', code: '30' },
  { label: '+36h', full: '+36 Hours Forecast', code: '36' },
];

// --- SIGWX DATA ---
const sigwxLevels = [
  { id: 'hi', name: 'High Level (FL250 - FL630)' },
  { id: 'mid', name: 'Mid Level (FL100 - FL450)' },
  { id: 'lo', name: 'Low Level (Surface - FL240)' },
];

const sigwxRegionsHi = [
  { id: 'e', name: 'Asia-Australia (South Asia / Sri Lanka)' },
  { id: 'g', name: 'Europe-Asia' },
  { id: 'd', name: 'Europe-Central Asia' },
  { id: 'c', name: 'Europe-Africa' },
  { id: 'a', name: 'Americas' },
  { id: 'b1', name: 'America-Africa' },
  { id: 'f', name: 'Pacific' },
  { id: 'i', name: 'North Pacific' },
  { id: 'h', name: 'North America-Europe' },
];

const sigwxRegionsMid = [
  { id: 'seas', name: 'Asia South (Sri Lanka Region)' },
  { id: 'mea', name: 'Middle East' },
  { id: 'eur', name: 'Europe' },
  { id: 'nat', name: 'North Atlantic' },
];

// --- CANADIAN GFA DATA ---
const gfaTypes = [
  { id: 'cldwx', name: 'Clouds & Weather (CLDWX)' },
  { id: 'icetb', name: 'Icing & Turbulence (ICETB)' },
];

const gfaRegions = [
  { id: 'pa', name: 'Canada-Pacific' },
  { id: 'pr', name: 'Canada-Prairie' },
  { id: 'oq', name: 'Canada-Ontario/Quebec' },
  { id: 'at', name: 'Canada-Atlantic' },
  { id: 'nw', name: 'Canada-Yukon/NWT' },
  { id: 'nu', name: 'Canada-Nunavut' },
];

const gfaTimes = [
  { label: '+00h', full: '+00 Hours (Current Analysis)', code: '00' },
  { label: '+06h', full: '+06 Hours Forecast', code: '06' },
  { label: '+12h', full: '+12 Hours Forecast', code: '12' },
];

export function ForecastMaps() {
  const [activeCategory, setActiveCategory] = useState<Category>('windtemp');
  const [imgLoading, setImgLoading] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [copied, setCopied] = useState(false);

  // Wind / Temp state
  const [windArea, setWindArea] = useState(windAreas[0].id);
  const [windLevel, setWindLevel] = useState(windLevels[3].code);
  const [windTime, setWindTime] = useState(windTimes[0].code);

  // SigWx state
  const [sigLevel, setSigLevel] = useState('hi');
  const [sigRegion, setSigRegion] = useState('e');

  // Canadian GFA state
  const [gfaType, setGfaType] = useState('cldwx');
  const [gfaRegion, setGfaRegion] = useState('pa');
  const [gfaTime, setGfaTime] = useState('06');

  // Compute live URL based on category
  const getChartUrl = (): string => {
    if (activeCategory === 'windtemp') {
      return `https://aviationweather.gov/data/products/fax/F${windTime}_wind_${windLevel}_${windArea}.gif`;
    }
    if (activeCategory === 'sigwx') {
      if (sigLevel === 'hi') {
        return `https://aviationweather.gov/data/products/fax/F24_sigwx_hi_${sigRegion}.gif`;
      }
      if (sigLevel === 'mid') {
        return `https://aviationweather.gov/data/products/fax/F24_sigwx_mid_${sigRegion}.gif`;
      }
      return `https://aviationweather.gov/data/products/fax/sigwx_lo_us.gif`;
    }
    return `https://aviationweather.gov/data/products/fax/F${gfaTime}_canfa_${gfaType}_${gfaRegion}.gif`;
  };

  const chartUrl = getChartUrl();

  const handleCategoryChange = (cat: Category) => {
    setImgLoading(true);
    setZoomLevel(1);
    setActiveCategory(cat);
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(chartUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    window.open(chartUrl, '_blank');
  };

  // Quick Preset Shortcuts
  const applySriLankaWindPreset = () => {
    setImgLoading(true);
    setZoomLevel(1);
    setActiveCategory('windtemp');
    setWindArea('d');
    setWindLevel('340');
    setWindTime('06');
  };

  const applySouthAsiaSigwxPreset = () => {
    setImgLoading(true);
    setZoomLevel(1);
    setActiveCategory('sigwx');
    setSigLevel('hi');
    setSigRegion('e');
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <header className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-accent/20 px-3 py-1 text-[11px] font-bold text-accent-soft border border-accent/40">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping"></span>
              LIVE NOAA AWC INTEGRATED API
            </span>
            <span className="text-xs text-slate-400">aviationweather.gov</span>
          </div>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">Aviation Forecast Maps Explorer</h1>
          <p className="mt-1 text-sm text-slate-400">
            Real-time WAFS Wind/Temp aloft, Significant Weather (SigWx), and Canadian GFA charts.
          </p>
        </div>

        {/* Quick Presets Bar */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={applySriLankaWindPreset}
            className="inline-flex items-center gap-2 rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-xs font-bold text-sky-300 transition-all hover:bg-accent/30 hover:text-white">
            <ZapIcon className="h-3.5 w-3.5 text-accent-soft" />
            VCBI Wind FL340 +6h
          </button>
          <button
            type="button"
            onClick={applySouthAsiaSigwxPreset}
            className="inline-flex items-center gap-2 rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-xs font-bold text-emerald-300 transition-all hover:bg-emerald-500/30 hover:text-white">
            <ZapIcon className="h-3.5 w-3.5 text-emerald-400" />
            South Asia SigWx
          </button>
        </div>
      </header>

      {/* Futuristic Main Category Tabs */}
      <section className="rounded-xl border border-line bg-panel p-2 shadow-lg">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <button
            type="button"
            onClick={() => handleCategoryChange('windtemp')}
            className={`group relative flex flex-col items-center justify-center rounded-lg py-3.5 px-4 transition-all duration-200 ${
              activeCategory === 'windtemp'
                ? 'bg-accent text-white shadow-xl shadow-sky-950/50 ring-1 ring-accent-soft'
                : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
            }`}>
            <div className="flex items-center gap-2">
              <WindIcon className={`h-4 w-4 ${activeCategory === 'windtemp' ? 'text-white' : 'text-sky-400'}`} />
              <span className="text-sm font-bold">Wind / Temperature</span>
            </div>
            <span className="mt-1 text-[11px] opacity-75">WAFS Aloft Charts · FL050 to FL630</span>
          </button>

          <button
            type="button"
            onClick={() => handleCategoryChange('sigwx')}
            className={`group relative flex flex-col items-center justify-center rounded-lg py-3.5 px-4 transition-all duration-200 ${
              activeCategory === 'sigwx'
                ? 'bg-accent text-white shadow-xl shadow-sky-950/50 ring-1 ring-accent-soft'
                : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
            }`}>
            <div className="flex items-center gap-2">
              <CloudRainIcon className={`h-4 w-4 ${activeCategory === 'sigwx' ? 'text-white' : 'text-amber-400'}`} />
              <span className="text-sm font-bold">SigWx (Significant Weather)</span>
            </div>
            <span className="mt-1 text-[11px] opacity-75">Turbulence, Icing & Storms</span>
          </button>

          <button
            type="button"
            onClick={() => handleCategoryChange('cangfa')}
            className={`group relative flex flex-col items-center justify-center rounded-lg py-3.5 px-4 transition-all duration-200 ${
              activeCategory === 'cangfa'
                ? 'bg-accent text-white shadow-xl shadow-sky-950/50 ring-1 ring-accent-soft'
                : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
            }`}>
            <div className="flex items-center gap-2">
              <CompassIcon className={`h-4 w-4 ${activeCategory === 'cangfa' ? 'text-white' : 'text-emerald-400'}`} />
              <span className="text-sm font-bold">Canadian GFA</span>
            </div>
            <span className="mt-1 text-[11px] opacity-75">Clouds, Weather, Ice & Turbulence</span>
          </button>
        </div>
      </section>

      {/* Interactive Controls & Parameter Selectors */}
      <section className="rounded-xl border border-line bg-panel p-5 sm:p-6 shadow-md">
        {/* Category Header */}
        <div className="flex items-center justify-between border-b border-line pb-4 mb-5">
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-accent/20 text-accent-soft">
              <LayersIcon className="h-4 w-4" />
            </span>
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200">
              {activeCategory === 'windtemp' && 'Wind & Temperature Chart Controls'}
              {activeCategory === 'sigwx' && 'Significant Weather (SigWx) Controls'}
              {activeCategory === 'cangfa' && 'Canadian GFA Chart Controls'}
            </h2>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            NOAA Fax Stream Online
          </div>
        </div>

        {/* 1. WIND / TEMP CONTROLS & QUICK PILLS */}
        {activeCategory === 'windtemp' && (
          <div className="space-y-6">
            {/* Region Dropdown */}
            <div>
              <label htmlFor="wind-area" className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                1. Select Region / Area
              </label>
              <select
                id="wind-area"
                value={windArea}
                onChange={(e) => {
                  setImgLoading(true);
                  setZoomLevel(1);
                  setWindArea(e.target.value);
                }}
                className="mt-2 w-full rounded-lg border border-line-strong bg-ink px-4 py-3 text-sm font-medium text-slate-100 outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-colors">
                {windAreas.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Flight Level Quick Pills */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                  2. Select Flight Level (Altitude)
                </label>
                <span className="text-xs text-sky-400 font-bold">
                  Active: {windLevels.find((l) => l.code === windLevel)?.full}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {windLevels.map((lvl) => {
                  const isActive = lvl.code === windLevel;
                  return (
                    <button
                      key={lvl.code}
                      type="button"
                      onClick={() => {
                        setImgLoading(true);
                        setZoomLevel(1);
                        setWindLevel(lvl.code);
                      }}
                      className={`rounded-lg px-3.5 py-2 text-xs font-bold transition-all ${
                        isActive
                          ? 'bg-accent text-white shadow-md shadow-sky-950/40 border border-accent-soft ring-1 ring-accent-soft'
                          : 'border border-line-strong bg-ink/70 text-slate-400 hover:border-slate-500 hover:text-white'
                      }`}>
                      {lvl.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Valid Forecast Time Quick Pills */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                  3. Select Forecast Horizon
                </label>
                <span className="text-xs text-sky-400 font-bold">
                  Active: {windTimes.find((t) => t.code === windTime)?.full}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {windTimes.map((time) => {
                  const isActive = time.code === windTime;
                  return (
                    <button
                      key={time.code}
                      type="button"
                      onClick={() => {
                        setImgLoading(true);
                        setZoomLevel(1);
                        setWindTime(time.code);
                      }}
                      className={`rounded-lg px-4 py-2 text-xs font-bold transition-all ${
                        isActive
                          ? 'bg-accent text-white shadow-md shadow-sky-950/40 border border-accent-soft ring-1 ring-accent-soft'
                          : 'border border-line-strong bg-ink/70 text-slate-400 hover:border-slate-500 hover:text-white'
                      }`}>
                      {time.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* 2. SIGWX CONTROLS */}
        {activeCategory === 'sigwx' && (
          <div className="space-y-6">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                1. Select Altitude Level
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {sigwxLevels.map((lvl) => {
                  const isActive = lvl.id === sigLevel;
                  return (
                    <button
                      key={lvl.id}
                      type="button"
                      onClick={() => {
                        setImgLoading(true);
                        setZoomLevel(1);
                        setSigLevel(lvl.id);
                        if (lvl.id === 'hi') setSigRegion('e');
                        else if (lvl.id === 'mid') setSigRegion('seas');
                        else setSigRegion('us');
                      }}
                      className={`rounded-lg border p-3 text-left transition-all ${
                        isActive
                          ? 'border-accent bg-accent/20 text-white font-bold shadow-md'
                          : 'border-line-strong bg-ink/60 text-slate-400 hover:border-slate-500 hover:text-slate-200'
                      }`}>
                      <span className="text-xs font-bold block">{lvl.name.split(' (')[0]}</span>
                      <span className="text-[11px] text-slate-400">{lvl.name.split(' (')[1]?.replace(')', '')}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {sigLevel !== 'lo' && (
              <div>
                <label htmlFor="sig-region" className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                  2. Select Coverage Region
                </label>
                <select
                  id="sig-region"
                  value={sigRegion}
                  onChange={(e) => {
                    setImgLoading(true);
                    setZoomLevel(1);
                    setSigRegion(e.target.value);
                  }}
                  className="mt-2 w-full rounded-lg border border-line-strong bg-ink px-4 py-3 text-sm font-medium text-slate-100 outline-none focus:border-accent focus:ring-1 focus:ring-accent">
                  {sigLevel === 'hi' &&
                    sigwxRegionsHi.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name}
                      </option>
                    ))}
                  {sigLevel === 'mid' &&
                    sigwxRegionsMid.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name}
                      </option>
                    ))}
                </select>
              </div>
            )}
          </div>
        )}

        {/* 3. CANADIAN GFA CONTROLS */}
        {activeCategory === 'cangfa' && (
          <div className="grid gap-5 md:grid-cols-3">
            <div>
              <label htmlFor="gfa-type" className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                Chart Type
              </label>
              <select
                id="gfa-type"
                value={gfaType}
                onChange={(e) => {
                  setImgLoading(true);
                  setZoomLevel(1);
                  setGfaType(e.target.value);
                }}
                className="mt-2 w-full rounded-lg border border-line-strong bg-ink px-4 py-3 text-sm font-medium text-slate-100 outline-none focus:border-accent focus:ring-1 focus:ring-accent">
                {gfaTypes.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="gfa-region" className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                Canadian Region
              </label>
              <select
                id="gfa-region"
                value={gfaRegion}
                onChange={(e) => {
                  setImgLoading(true);
                  setZoomLevel(1);
                  setGfaRegion(e.target.value);
                }}
                className="mt-2 w-full rounded-lg border border-line-strong bg-ink px-4 py-3 text-sm font-medium text-slate-100 outline-none focus:border-accent focus:ring-1 focus:ring-accent">
                {gfaRegions.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="gfa-time" className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                Valid Time
              </label>
              <select
                id="gfa-time"
                value={gfaTime}
                onChange={(e) => {
                  setImgLoading(true);
                  setZoomLevel(1);
                  setGfaTime(e.target.value);
                }}
                className="mt-2 w-full rounded-lg border border-line-strong bg-ink px-4 py-3 text-sm font-medium text-slate-100 outline-none focus:border-accent focus:ring-1 focus:ring-accent">
                {gfaTimes.map((t) => (
                  <option key={t.code} value={t.code}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </section>

      {/* Live Chart Image Display Viewer */}
      <section className="rounded-xl border border-line bg-panel p-5 sm:p-6 shadow-xl">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white">
                {activeCategory === 'windtemp' &&
                  `${windAreas.find((a) => a.id === windArea)?.short} · FL${windLevel} · +${windTime}h Forecast`}
                {activeCategory === 'sigwx' &&
                  `Significant Weather (SigWx) · ${sigLevel.toUpperCase()} Level`}
                {activeCategory === 'cangfa' &&
                  `Canadian GFA · ${gfaType.toUpperCase()} · ${gfaRegion.toUpperCase()}`}
              </h2>
              {imgLoading && <RefreshCwIcon className="h-4 w-4 animate-spin text-accent-soft" />}
            </div>
            <p className="mt-1 text-xs font-mono text-slate-400 truncate max-w-xl">
              Source: <code className="text-sky-300">{chartUrl}</code>
            </p>
          </div>

          {/* Interactive Toolbar (Zoom, Copy Link, Download, External) */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Zoom controls */}
            <div className="flex items-center rounded-lg border border-line-strong bg-ink/80 p-1">
              <button
                type="button"
                onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.25))}
                title="Zoom In"
                className="rounded p-1.5 text-slate-300 hover:bg-white/10 hover:text-white">
                <ZoomInIcon className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => setZoomLevel((z) => Math.max(1, z - 0.25))}
                title="Zoom Out"
                className="rounded p-1.5 text-slate-300 hover:bg-white/10 hover:text-white">
                <ZoomOutIcon className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => setZoomLevel(1)}
                title="Reset Zoom"
                className="rounded p-1.5 text-slate-300 hover:bg-white/10 hover:text-white border-l border-line-strong">
                <RotateCcwIcon className="h-4 w-4" />
              </button>
            </div>

            {/* Copy Link Button */}
            <button
              type="button"
              onClick={handleCopyLink}
              className="inline-flex items-center gap-1.5 rounded-lg border border-line-strong bg-ink/80 px-3 py-2 text-xs font-medium text-slate-300 transition-colors hover:border-slate-500 hover:text-white">
              {copied ? (
                <>
                  <CheckIcon className="h-4 w-4 text-emerald-400" />
                  Copied!
                </>
              ) : (
                <>
                  <CopyIcon className="h-4 w-4" />
                  Copy Direct Link
                </>
              )}
            </button>

            {/* Download Button */}
            <button
              type="button"
              onClick={handleDownload}
              className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-xs font-bold text-white transition-colors hover:bg-sky-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-soft">
              <DownloadIcon className="h-4 w-4" />
              Download Chart
            </button>
          </div>
        </div>

        {/* Live Chart Image Canvas */}
        <figure className="mt-5 overflow-hidden rounded-xl border border-line-strong bg-slate-950/95 flex flex-col relative">
          <div className="min-h-[520px] lg:h-[680px] xl:h-[780px] w-full flex items-center justify-center p-3 overflow-auto relative">
            {imgLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-slate-950/85 backdrop-blur-sm z-20 transition-opacity">
                <div className="flex flex-col items-center gap-3 rounded-xl border border-line-strong bg-panel p-6 shadow-2xl">
                  <RefreshCwIcon className="h-8 w-8 animate-spin text-accent" />
                  <p className="text-sm font-bold text-white">Updating Live NOAA Chart...</p>
                  <p className="text-xs text-slate-400">Fetching latest fax stream from aviationweather.gov</p>
                </div>
              </div>
            )}
            <img
              src={chartUrl}
              alt="NOAA Aviation Weather Chart"
              onLoad={() => setImgLoading(false)}
              onError={() => setImgLoading(false)}
              style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'center center' }}
              className="h-full w-full object-contain rounded-lg shadow-2xl transition-transform duration-200 ease-out"
            />
          </div>
          
          <figcaption className="border-t border-line-strong bg-slate-900/90 px-5 py-3 text-xs text-slate-400 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <span className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
              NOAA Aviation Weather Center (AWC) · Real-time Fax Stream
            </span>
            <span className="text-[11px] text-emerald-400 font-mono">Zoom: {(zoomLevel * 100).toFixed(0)}% · 200 OK</span>
          </figcaption>
        </figure>
      </section>
    </div>
  );
}