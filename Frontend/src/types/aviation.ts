export type BriefingStatus = 'Draft' | 'Approved' | 'Pending' | 'Generated' | 'Valid' | 'Expired';

export interface BriefingDocument {
  reference: string;
  route: string;
  forecastDate: string;
  status: BriefingStatus;
  url?: string;
}

export interface FlightStat {
  label: string;
  value: string;
  icon: 'route' | 'duration' | 'distance' | 'aircraft' | 'terminal';
}

export interface WeatherMetric {
  label: string;
  value: string;
  detail: string;
  icon: 'wind' | 'visibility' | 'temperature' | 'cloud';
}

export interface BriefingRow {
  label: string;
  value: string;
}