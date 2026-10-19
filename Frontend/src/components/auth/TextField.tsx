import React, { useState } from 'react';
import { EyeIcon, EyeOffIcon } from 'lucide-react';

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
  const isPassword = type === 'password';
  const [showPassword, setShowPassword] = useState(false);
  const inputType = isPassword && showPassword ? 'text' : type;

  return (
    <div>
      <label htmlFor={id} className="block text-xs text-slate-400">
        {label}
      </label>
      <div className="relative mt-2">
        <input
          id={id}
          type={inputType}
          value={value}
          required={required}
          placeholder={placeholder}
          autoComplete={autoComplete}
          onChange={(event) => onChange(event.target.value)}
          className={`w-full rounded-lg border border-line-strong bg-ink px-3 py-2.5 text-sm text-slate-100 outline-none transition-colors placeholder:text-slate-600 focus:border-accent ${isPassword ? 'pr-10' : ''}`} />

        {isPassword ?
        <button
          type="button"
          id={`${id}-visibility-toggle`}
          onClick={() => setShowPassword((prev) => !prev)}
          aria-label={showPassword ? 'Hide password' : 'Show password'}
          aria-pressed={showPassword}
          title={showPassword ? 'Hide password' : 'Show password'}
          className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-500 transition-colors hover:text-slate-200 focus:outline-none focus-visible:text-accent">

            {showPassword ?
          <EyeOffIcon className="h-4 w-4" aria-hidden="true" /> :
          <EyeIcon className="h-4 w-4" aria-hidden="true" />}
          </button> :
        null}
      </div>

      {hint ? <p className="mt-1.5 text-[11px] text-slate-500">{hint}</p> : null}
    </div>);

}