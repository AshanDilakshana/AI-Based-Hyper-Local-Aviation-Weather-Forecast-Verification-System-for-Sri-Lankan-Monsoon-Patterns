import React from 'react';

type SwitchProps = {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  description?: string;
};

export function Switch({ checked, onChange, label, description }: SwitchProps) {
  return (
    <div className="flex items-start justify-between gap-4 py-3">
      <span className="min-w-0">
        <span className="block text-sm font-medium text-slate-100">{label}</span>
        {description ? <span className="mt-0.5 block text-xs text-slate-500">{description}</span> : null}
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        onClick={() => onChange(!checked)}
        className={`relative h-6 w-11 shrink-0 rounded-full border transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
        checked ? 'border-accent bg-accent' : 'border-line-strong bg-inset'}`
        }>
        
        <span
          className={`absolute top-0.5 h-4 w-4 rounded-full bg-white transition-transform duration-150 ease-out ${
          checked ? 'translate-x-6' : 'translate-x-1'}`
          }
          style={{ backgroundColor: checked ? '#FFFFFF' : undefined }}
          aria-hidden="true" />
        
      </button>
    </div>);

}