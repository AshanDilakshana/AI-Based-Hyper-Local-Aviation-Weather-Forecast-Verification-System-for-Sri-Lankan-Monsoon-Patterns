import React, { useId } from 'react';

type SparklineProps = {
  points: number[];
  color: string;
  height?: number;
  ariaLabel: string;
  showAxes?: boolean;
  xLabels?: string[];
  yFormatter?: (val: number) => string;
};

export function Sparkline({ points, color, height = 48, ariaLabel, showAxes = false, xLabels, yFormatter = (v) => v.toString() }: SparklineProps) {
  const gradientId = useId();
  const width = 100;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;

  const coords = points.map((point, index) => {
    const x = index / (points.length - 1) * width;
    const y = height - (point - min) / range * (height - 8) - 4;
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  });

  const line = `M ${coords.join(' L ')}`;
  const area = `${line} L ${width},${height} L 0,${height} Z`;

  const chart = (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className="w-full"
      style={{ height }}
      role="img"
      aria-label={ariaLabel}>
      
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.22" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gradientId})`} />
      <path
        d={line}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke" />
    </svg>
  );

  if (!showAxes) return chart;

  return (
    <div className="flex flex-col w-full text-[10px] text-slate-400 font-mono">
      <div className="flex">
        <div className="flex flex-col justify-between pr-3 text-right w-12 shrink-0 py-[2px]" style={{ height }}>
          <span>{yFormatter(max)}</span>
          <span>{yFormatter(min)}</span>
        </div>
        <div className="flex-1 relative">
           {/* Top and bottom dashed grid lines */}
           <div className="absolute top-0 left-0 w-full h-[1px] bg-line border-dashed opacity-50 pointer-events-none" />
           <div className="absolute bottom-0 left-0 w-full h-[1px] bg-line border-dashed opacity-50 pointer-events-none" />
           {chart}
        </div>
      </div>
      
      {xLabels && xLabels.length > 0 && (
        <div className="flex justify-between pl-12 pt-2 pr-1">
          <span>{xLabels[0]}</span>
          {xLabels.length > 2 && <span>{xLabels[Math.floor((xLabels.length - 1) / 2)]}</span>}
          <span>{xLabels[xLabels.length - 1]}</span>
        </div>
      )}
    </div>
  );

}