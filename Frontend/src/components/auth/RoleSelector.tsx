import React from 'react';
import { PlaneIcon, RadarIcon, ShieldIcon } from 'lucide-react';
import type { Role } from '../../types/auth';
import { roleMeta } from '../../types/auth';

type RoleSelectorProps = {
  value: Role;
  onChange: (role: Role) => void;
};

const icons: Record<Role, typeof PlaneIcon> = {
  forecaster: RadarIcon,
  pilot: PlaneIcon,
  admin: ShieldIcon
};

export function RoleSelector({ value, onChange }: RoleSelectorProps) {
  return (
    <fieldset>
      <legend className="text-xs text-slate-400">Sign in as</legend>
      <div className="mt-2 grid grid-cols-1 sm:grid-cols-3 gap-3">
        {(Object.keys(roleMeta) as Role[]).map((role) => {
          const Icon = icons[role];
          const isActive = role === value;
          return (
            <button
              key={role}
              type="button"
              onClick={() => onChange(role)}
              aria-pressed={isActive}
              className={`rounded-lg border p-3 text-left transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
              isActive ?
              'border-accent bg-accent/10' :
              'border-line-strong hover:border-slate-500'}`
              }>
              
              <span className="flex items-center gap-2">
                <Icon
                  className={`h-4 w-4 ${isActive ? 'text-accent-soft' : 'text-slate-500'}`}
                  aria-hidden="true" />
                
                <span className={`text-sm font-semibold ${isActive ? 'text-white' : 'text-slate-300'}`}>
                  {roleMeta[role].label}
                </span>
              </span>
              <span className="mt-1.5 block text-[11px] leading-relaxed text-slate-500">
                {roleMeta[role].blurb}
              </span>
            </button>);

        })}
      </div>
    </fieldset>);

}