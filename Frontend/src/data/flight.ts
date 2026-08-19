import type { BriefingRow, FlightStat, WeatherMetric } from '../types/aviation';

export const flightStats: FlightStat[] = [
{ label: 'Route', value: 'CMB → SIN', icon: 'route' },
{ label: 'Flight duration', value: '3h 48m', icon: 'duration' },
{ label: 'Great-circle distance', value: '1,706 nm', icon: 'distance' },
{ label: 'Aircraft Number', value: '4R-ANA', icon: 'aircraft' }];


export const forecastStats: FlightStat[] = [
{ label: 'Route', value: 'CMB → SIN', icon: 'route' },
{ label: 'Flight duration', value: '3h 48m', icon: 'duration' },
{ label: 'Great-circle distance', value: '1,706 nm', icon: 'distance' },
{ label: 'Departure terminal', value: 'Terminal 1', icon: 'terminal' }];


export const weatherMetrics: WeatherMetric[] = [
{ label: 'Wind', value: '14 kt', detail: '240° WSW', icon: 'wind' },
{ label: 'Headwind', value: '8 kt', detail: 'Runway 04 component', icon: 'wind' },
{ label: 'Crosswind', value: '4 kt', detail: 'Runway 04 component', icon: 'wind' },
{ label: 'Visibility', value: '10 km', detail: 'VMC conditions', icon: 'visibility' },
{ label: 'Temperature', value: '29°C', detail: 'Feels like 32°', icon: 'temperature' },
{ label: 'Cloud base', value: '2,500 ft', detail: 'SCT 035', icon: 'cloud' }];


export const briefingRows: BriefingRow[] = [
{ label: 'Departure weather', value: 'VMC · scattered cloud at 2,500 ft' },
{ label: 'En-route conditions', value: 'Light turbulence expected FL280–320' },
{ label: 'Destination weather', value: 'TEMPO SHRA after 18:00 UTC' },
{ label: 'Pressure / humidity', value: '1009 hPa · 78%' }];


export const flightLevels: string[] = [
'FL630',
'FL450',
'FL390',
'FL340',
'FL300',
'FL240',
'FL180',
'FL100',
'FL050'];


export const requestMaps: string[] = ['WIND/TEMPERATURES', 'ICAO AREA D SIGWX'];

export const requestPreview: BriefingRow[] = [
{ label: 'Route', value: 'VCBI → WSSS' },
{ label: 'Forecast scope', value: 'Departure, en-route, destination' },
{ label: 'Approval routing', value: 'BIA Met Forecast Desk' }];


export const routeMapImage = "/ee0d623a-21d2-486d-bada-bc88b8876581.jpg";