import React from 'react';

type SegmentedControlProps = {
  options: string[];
  value: string;
  onChange: (value: string) => void;
  label: string;
};

export function SegmentedControl({ options, value, onChange, label }: SegmentedControlProps) {
  return (
    <div
      role="group"
      aria-label={label}
      className="inline-flex items-center gap-1 rounded-lg border border-line-strong p-1">
      
      {options.map((option) => {
        const isActive = option === value;
        return (
          <button
            key={option}
            type="button"
            onClick={() => onChange(option)}
            aria-pressed={isActive}
            className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
            isActive ? 'bg-accent text-white' : 'text-slate-400 hover:text-slate-200'}`
            }>
            
            {option}
          </button>);

      })}
    </div>);

}