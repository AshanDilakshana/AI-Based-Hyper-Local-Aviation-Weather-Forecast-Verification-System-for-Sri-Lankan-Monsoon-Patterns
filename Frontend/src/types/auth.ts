export type Role = 'forecaster' | 'pilot';

export type AuthUser = {
  name: string;
  initials: string;
  role: Role;
  title: string;
  reference: string;
  email: string;
  phone: string;
  organisation: string;
  station: string;
};

export const roleMeta: Record<Role, {label: string;title: string;home: string;blurb: string;}> = {
  forecaster: {
    label: 'Forecaster',
    title: 'Meteorological Officer',
    home: '/',
    blurb: 'Issue observations, run hyper-local models and publish aerodrome forecasts.'
  },
  pilot: {
    label: 'Pilot',
    title: 'Flight Crew',
    home: '/pilot',
    blurb: 'Read current aerodrome conditions and download wind & temp aloft charts.'
  }
};