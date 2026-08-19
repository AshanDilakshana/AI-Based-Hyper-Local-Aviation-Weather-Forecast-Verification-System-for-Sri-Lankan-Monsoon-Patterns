export type Observation = {
  time: string;
  temperature: string;
  pressure: string;
  humidity: string;
  windSpeed: string;
  windDirection: string;
  visibility: string;
  cloudCoverage: string;
  rainfall: string;
};

export type MetricTone = 'amber' | 'sky' | 'cyan' | 'emerald' | 'slate' | 'green';

export type Metric = {
  label: string;
  value: string;
  unit?: string;
  footnote?: string;
  tone: MetricTone;
};

export type Series = {
  label: string;
  value: string;
  color: string;
  points: number[];
};