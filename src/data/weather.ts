import type { Metric, Observation, Series } from '../types/weather';

export const STATION = {
  fir: 'VCCC · Colombo FIR',
  airport: 'Bandaranaike International Airport',
  codes: 'CMB / VCBI'
};

export const LAST_UPDATED = '1103 UTC 11 Tue Aug 2026';

export const currentMetrics: Metric[] = [
{ label: 'Temperature', value: '29.2', unit: '°C', footnote: '↑ 0.8°', tone: 'amber' },
{ label: 'Wind speed', value: '14', unit: 'kt', footnote: 'WSW 240°', tone: 'emerald' },
{ label: 'Humidity', value: '78', unit: '% RH', footnote: '↑ 3%', tone: 'cyan' },
{ label: 'Cloud base', value: 'BKN', unit: '2500', footnote: 'BKN scattered layers', tone: 'slate' },
{ label: 'Visibility', value: '10 km', footnote: '9999+', tone: 'green' },
{ label: 'Pressure', value: '1009.4', unit: 'hPa', footnote: '↓ 1.2', tone: 'sky' }];


export const recentObservations: Observation[] = [
{
  time: '08:30',
  temperature: '29.2 °C',
  pressure: '1009.4 hPa',
  humidity: '78%',
  windSpeed: '14 kt',
  windDirection: '240° WSW',
  visibility: '10 km',
  cloudCoverage: 'SCT 035',
  rainfall: '0.0 mm'
},
{
  time: '08:15',
  temperature: '29.0 °C',
  pressure: '1009.5 hPa',
  humidity: '79%',
  windSpeed: '13 kt',
  windDirection: '238° WSW',
  visibility: '10 km',
  cloudCoverage: 'SCT 035',
  rainfall: '0.0 mm'
},
{
  time: '08:00',
  temperature: '28.8 °C',
  pressure: '1009.6 hPa',
  humidity: '80%',
  windSpeed: '12 kt',
  windDirection: '235° SW',
  visibility: '9 km',
  cloudCoverage: 'BKN 030',
  rainfall: '0.2 mm'
},
{
  time: '07:45',
  temperature: '28.7 °C',
  pressure: '1009.7 hPa',
  humidity: '81%',
  windSpeed: '11 kt',
  windDirection: '232° SW',
  visibility: '9 km',
  cloudCoverage: 'BKN 030',
  rainfall: '0.4 mm'
},
{
  time: '07:30',
  temperature: '28.5 °C',
  pressure: '1009.9 hPa',
  humidity: '82%',
  windSpeed: '10 kt',
  windDirection: '228° SW',
  visibility: '8 km',
  cloudCoverage: 'BKN 028',
  rainfall: '0.8 mm'
},
{
  time: '07:15',
  temperature: '28.4 °C',
  pressure: '1010.0 hPa',
  humidity: '83%',
  windSpeed: '9 kt',
  windDirection: '225° SW',
  visibility: '8 km',
  cloudCoverage: 'BKN 028',
  rainfall: '1.1 mm'
}];


export const forecastRows: Observation[] = recentObservations.map((row, index) => ({
  ...row,
  time: ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00'][index]
}));

export const trendSeries: Series[] = [
{
  label: 'Temperature',
  value: '29.2°C',
  color: '#FBBF24',
  points: [28.4, 28.5, 28.5, 28.7, 28.6, 28.9, 29.0, 28.9, 29.1, 29.2]
},
{
  label: 'wind',
  value: '78%',
  color: '#22D3EE',
  points: [9, 9.5, 10, 11, 10.6, 12, 12.4, 12.1, 13.2, 14]
},
{
  label: 'Pressure',
  value: '1009.4 hPa',
  color: '#38BDF8',
  points: [1010, 1010, 1009.9, 1009.8, 1009.8, 1009.7, 1009.6, 1009.6, 1009.5, 1009.4]
}];


export const historicalSeries: Series[] = [
{
  label: 'Temperature',
  value: '29.2°C',
  color: '#FBBF24',
  points: [28.3, 28.6, 28.4, 28.9, 28.7, 29.1, 28.9, 29.2]
},
{
  label: 'Pressure',
  value: '1009.4 hPa',
  color: '#38BDF8',
  points: [1010.2, 1010.1, 1009.9, 1009.9, 1009.7, 1009.6, 1009.5, 1009.4]
},
{
  label: 'Humidity',
  value: '78% RH',
  color: '#22D3EE',
  points: [84, 83, 82.5, 82, 81, 80, 79, 78]
}];


export const forecastDetails: {label: string;value: string;}[] = [
{ label: 'Forecast ID', value: 'AIV-2026-0618-0830' },
{ label: 'Created time', value: '18 Jun 2026 · 08:30 SLST' },
{ label: 'Latest API data timestamp', value: '18 Jun 2026 · 08:30 SLST' },
{ label: 'Coverage', value: 'Bandaranaike Intl. Airport (VCBI)' },
{ label: 'Prediction period', value: 'Next 3-hour aviation forecast' }];


export const forecastMetrics: Metric[] = [
{ label: 'Temperature', value: '29.2', unit: '°C', footnote: '↑ 0.8°', tone: 'amber' },
{ label: 'Wind speed', value: '14', unit: 'kt', footnote: 'WSW 240°', tone: 'emerald' },
{ label: 'Humidity', value: '78', unit: '% RH', footnote: '↑ 3%', tone: 'cyan' },
{ label: 'Cloud base', value: 'BKN', unit: '2500', footnote: 'BKN scattered layers', tone: 'slate' },
{ label: 'Visibility', value: '+10 km', footnote: '9999+', tone: 'green' },
{ label: 'Pressure', value: '1009.4', unit: 'hPa', footnote: '↓ 1.2', tone: 'sky' }];