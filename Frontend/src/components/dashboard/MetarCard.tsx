import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';

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
  lastUpdatedText
}: MetarCardProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const formatVisibility = (vis: number) => {
    if (vis == null) return '--';
    if (vis >= 9999) return '≥10 km';
    return `${(vis / 1000).toFixed(1)} km`;
  };

  const padTime = (time?: string) => (time ? String(time).padStart(4, '0') : '0000');
  const formattedTime = padTime(timeUtc);
  
  // Format dates safely
  const safeDate = date instanceof Date && !isNaN(date.getTime()) ? date : new Date();
  const dateStr = safeDate.toLocaleDateString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short'
  });

  return (
    <div className={`relative overflow-hidden rounded-2xl shadow-lg border transition-colors ${
      isDark ? 'bg-panel-deep text-white border-line/60' : 'bg-slate-900 text-white border-line'
    }`}>
      {/* Background Image with Overlay */}
      <div 
        className="absolute inset-0 z-0 bg-cover bg-center opacity-60"
        style={{ backgroundImage: 'url(https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=2074&auto=format&fit=crop)' }}
      />
      <div className={`absolute inset-0 z-0 transition-opacity duration-300 ${
        isDark 
          ? 'bg-gradient-to-t from-canvas/95 via-canvas/70 to-canvas/30' 
          : 'bg-gradient-to-t from-slate-950/70 via-slate-900/40 to-slate-900/20'
      }`} />

      <div className="relative z-10 p-6">
        {/* Top Section */}
        <div>
          <p className="text-yellow-500 font-semibold text-sm mb-1 tracking-wide drop-shadow-sm">
            VCBI · Katunayake · RWY 04/22
          </p>
          <h2 className="text-3xl md:text-4xl font-bold mb-2 text-[#ffffff] drop-shadow-sm">Bandaranaike International</h2>
          <p className="text-[#ffffff] text-sm drop-shadow-sm opacity-90">
            {dateStr} · {formattedTime.slice(0, 2)}:{formattedTime.slice(2, 4)} Sri Lanka time · METAR {formattedTime}Z, received {lastUpdatedText}
          </p>
        </div>

        {/* Bottom Data Section */}
        <div className={`mt-8 rounded-xl p-5 backdrop-blur-md transition-colors duration-200 border shadow-sm ${
          isDark
            ? 'bg-panel/85 border-line text-white shadow-black/20'
            : 'bg-[#ffffff]/90 border-line text-slate-900 shadow-slate-200/50'
        }`}>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-6 text-center items-start">
            <div className="flex flex-col items-center justify-start text-center">
              <p className={`text-sm font-medium mb-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Wind</p>
              <p className={`text-xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{windDir != null ? `${windDir}°` : 'VRB'} {windSpeed != null ? `${windSpeed} kt` : '--'}</p>
            </div>
            <div className="flex flex-col items-center justify-start text-center">
              <p className={`text-sm font-medium mb-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Visibility</p>
              <p className={`text-xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{formatVisibility(visibility)}</p>
            </div>
            <div className="flex flex-col items-center justify-start text-center">
              <p className={`text-sm font-medium mb-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Ceiling</p>
              <p className={`text-xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{clouds === 'N/A' || !clouds ? 'None' : clouds.split(' ')[0]}</p>
              {clouds && clouds !== 'N/A' && clouds.split(' ').length > 1 && (
                <p className={`text-xs font-mono mt-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{clouds.split(' ').slice(1).join(' ')}</p>
              )}
            </div>
            <div className="flex flex-col items-center justify-start text-center">
              <p className={`text-sm font-medium mb-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>QNH</p>
              <p className={`text-xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{qnh != null ? `${qnh} hPa` : '--'}</p>
            </div>
            <div className="col-span-2 md:col-span-1 flex flex-col items-center justify-start text-center">
              <p className={`text-sm font-medium mb-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Temp / Dew</p>
              <p className={`text-xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{temp != null ? `${temp}°` : '--'} / {dew != null ? `${dew}°` : '--'}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
