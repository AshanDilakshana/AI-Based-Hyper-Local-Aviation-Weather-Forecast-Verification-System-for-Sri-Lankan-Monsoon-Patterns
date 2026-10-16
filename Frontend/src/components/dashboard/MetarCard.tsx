import React from 'react';

export interface MetarCardProps {
  timeUtc: string;
  date: Date;
  windDir: number | string;
  windSpeed: number;
  visibility: number;
  clouds?: string;
  qnh: number;
  temp: number;
  dew: number;
  rawMetar?: string;
  lastUpdatedText: string;
}

export function MetarCard({
  timeUtc,
  date,
  windDir,
  windSpeed,
  visibility,
  clouds = 'None',
  qnh,
  temp,
  dew,
  rawMetar,
  lastUpdatedText
}: MetarCardProps) {
  // Basic Flight Category Logic (simplified)
  // VFR: Visibility >= 8000m, Ceiling >= 3000ft (simplified to just check visibility here if ceiling isn't easily parsed)
  const isVfr = visibility >= 8000;
  const flightCategory = isVfr ? 'VFR' : 'IFR';
  const flightCategoryColor = isVfr ? 'text-green-700' : 'text-red-700';
  const flightCategoryIndicator = isVfr ? 'bg-green-700' : 'bg-red-700';

  const formatVisibility = (vis: number) => {
    if (vis >= 9999) return '≥10 km';
    return `${(vis / 1000).toFixed(1)} km`;
  };

  const padTime = (time: string) => time.padStart(4, '0');
  const formattedTime = padTime(timeUtc);
  
  // Format dates: "Thu 1 Oct"
  const dateStr = date.toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short'
  });

  const generatedMetar = rawMetar || `VCBI ${date.getDate().toString().padStart(2, '0')}${formattedTime}Z ${windDir.toString().padStart(3, '0')}${windSpeed.toString().padStart(2, '0')}KT ${visibility >= 9999 ? '9999' : visibility} ${clouds !== 'N/A' && clouds !== 'None' ? clouds : 'CAVOK'} ${Math.round(temp)}/${Math.round(dew)} Q${qnh} NOSIG`;

  return (
    <div className="relative overflow-hidden rounded-2xl bg-slate-800 text-white shadow-lg border border-slate-700">
      {/* Background Image with Overlay */}
      <div 
        className="absolute inset-0 z-0 bg-cover bg-center opacity-60"
        style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=2074&auto=format&fit=crop)' }}
      />
      <div className="absolute inset-0 z-0 bg-gradient-to-t from-slate-900/90 via-slate-800/60 to-slate-800/40" />

      <div className="relative z-10 p-6">
        {/* Top Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <p className="text-yellow-500 font-semibold text-sm mb-1 tracking-wide">
              VCBI · Katunayake · RWY 04/22
            </p>
            <h2 className="text-3xl md:text-4xl font-bold mb-2">Bandaranaike International</h2>
            <p className="text-slate-300 text-sm">
              {dateStr} · {formattedTime.slice(0, 2)}:{formattedTime.slice(2, 4)} Sri Lanka time · METAR {formattedTime}Z, received {lastUpdatedText}
            </p>
          </div>

          {/* Flight Category Badge */}
          <div className="bg-white rounded-xl p-3 flex items-center gap-3 shadow-sm">
            <div className={`w-1.5 h-12 rounded-full ${flightCategoryIndicator}`} />
            <div className="pr-4">
              <p className="text-slate-500 text-xs font-medium uppercase tracking-wider mb-0.5">Flight category now</p>
              <p className={`text-2xl font-bold ${flightCategoryColor}`}>{flightCategory}</p>
            </div>
          </div>
        </div>

        {/* Bottom Data Section */}
        <div className="mt-8 bg-slate-50/95 backdrop-blur-sm rounded-xl p-5 text-slate-900 shadow-inner">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-6 mb-6">
            <div>
              <p className="text-slate-500 text-sm font-medium mb-1">Wind</p>
              <p className="text-xl font-bold">{windDir}° {windSpeed} kt</p>
            </div>
            <div>
              <p className="text-slate-500 text-sm font-medium mb-1">Visibility</p>
              <p className="text-xl font-bold">{formatVisibility(visibility)}</p>
            </div>
            <div>
              <p className="text-slate-500 text-sm font-medium mb-1">Ceiling</p>
              <p className="text-xl font-bold">{clouds === 'N/A' || !clouds ? 'None' : clouds.split(' ')[0]}</p>
              {clouds && clouds !== 'N/A' && clouds.split(' ').length > 1 && (
                <p className="text-xs text-slate-500 font-mono mt-1">{clouds.split(' ').slice(1).join(' ')}</p>
              )}
            </div>
            <div>
              <p className="text-slate-500 text-sm font-medium mb-1">QNH</p>
              <p className="text-xl font-bold">{qnh} hPa</p>
            </div>
            <div>
              <p className="text-slate-500 text-sm font-medium mb-1">Temp / Dew</p>
              <p className="text-xl font-bold">{temp}° / {dew}°</p>
            </div>
          </div>

          {/* METAR String */}
          <div className="bg-slate-200/60 rounded-lg p-3">
            <p className="text-slate-700 font-mono text-sm tracking-wide overflow-x-auto whitespace-nowrap">
              {generatedMetar}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
