import React from 'react';

type TextFieldProps = {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
  autoComplete?: string;
  hint?: string;
  required?: boolean;
};

export function TextField({
  id,
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
  autoComplete,
  hint,
  required = true
}: TextFieldProps) {
  return (
    <div>
      <label htmlFor={id} className="block text-xs text-slate-400">
        {label}
      </label>
      <input
        id={id}
        type={type}
        value={value}
        required={required}
        placeholder={placeholder}
        autoComplete={autoComplete}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 w-full rounded-lg border border-line-strong bg-ink px-3 py-2.5 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-600 focus:border-accent" />
      
      {hint ? <p className="mt-1.5 text-[11px] text-slate-500">{hint}</p> : null}
    </div>);

}