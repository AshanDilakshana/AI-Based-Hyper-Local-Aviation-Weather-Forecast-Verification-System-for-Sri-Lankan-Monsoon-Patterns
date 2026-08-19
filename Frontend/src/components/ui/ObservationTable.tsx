import React from 'react';
import type { Observation } from '../../types/weather';

type ObservationTableProps = {
  rows: Observation[];
  timeLabel: string;
  caption: string;
};

const columns = [
'Temperature',
'Pressure',
'Humidity',
'Wind speed',
'Wind direction',
'Visibility',
'Cloud coverage',
'Rainfall'];


export function ObservationTable({ rows, timeLabel, caption }: ObservationTableProps) {
  return (
    <div className="-mx-1 overflow-x-auto px-1">
      <table className="w-full min-w-[900px] border-collapse text-left">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="border-b border-line">
            <th scope="col" className="pb-3 text-xs font-medium tracking-wide text-slate-500">
              {timeLabel}
            </th>
            {columns.map((column) =>
            <th key={column} scope="col" className="pb-3 text-xs font-medium tracking-wide text-slate-500">
                {column}
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) =>
          <tr key={row.time} className="border-b border-line-soft last:border-b-0">
              <th scope="row" className="py-3.5 text-xs font-semibold text-white">
                {row.time}
              </th>
              <td className="py-3.5 text-xs text-slate-300">{row.temperature}</td>
              <td className="py-3.5 text-xs text-slate-300">{row.pressure}</td>
              <td className="py-3.5 text-xs text-slate-300">{row.humidity}</td>
              <td className="py-3.5 text-xs text-slate-300">{row.windSpeed}</td>
              <td className="py-3.5 text-xs text-slate-300">{row.windDirection}</td>
              <td className="py-3.5 text-xs text-slate-300">{row.visibility}</td>
              <td className="py-3.5 text-xs text-slate-300">{row.cloudCoverage}</td>
              <td className="py-3.5 text-xs text-slate-300">{row.rainfall}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>);

}