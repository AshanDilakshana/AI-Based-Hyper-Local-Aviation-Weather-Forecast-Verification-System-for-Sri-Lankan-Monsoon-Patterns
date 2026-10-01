import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { AlertTriangleIcon, LogInIcon } from 'lucide-react';
import { AuthShell } from '../components/auth/AuthShell';
import { RoleSelector } from '../components/auth/RoleSelector';
import { TextField } from '../components/auth/TextField';
import { useAuth } from '../contexts/AuthContext';
import type { Role } from '../types/auth';
import { roleMeta } from '../types/auth';

type LocationState = {from?: string;} | null;

export function SignIn() {
  const [role, setRole] = useState<Role>('forecaster');
  const [reference, setReference] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }
    setError('');
    setSubmitting(true);
    
    try {
      await signIn({
        role,
        name: role === 'pilot' ? 'Capt. N. Fernando' : (role === 'admin' ? 'System Admin' : 'A. Ranasinghe'),
        reference,
        password: password,
        organisation: role === 'pilot' ? 'Airlines' : (role === 'admin' ? 'IT Dept' : 'Department of Meteorology'),
        station: 'VCBI · Bandaranaike Intl.'
      });
      navigate(state?.from ?? roleMeta[role].home, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthShell
      eyebrow="Secure access"
      title="Sign in to the console"
      description="Separate credentials are issued for meteorological officers and flight crew."
      footer={
      <>
          Need an account?{' '}
          <Link
          to="/sign-up"
          className="font-semibold text-accent-pale underline-offset-4 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-accent">
          
            Request access
          </Link>
        </>
      }>
      
      <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
        <RoleSelector value={role} onChange={setRole} />

        {role === 'forecaster' ?
        <>
            <TextField
            id="metId"
            label="Met Officer ID"
            value={reference}
            onChange={setReference}
            placeholder="MET-04821"
            autoComplete="username" />
          
          </> : role === 'admin' ? 
        <>
            <TextField
            id="adminId"
            label="Admin ID"
            value={reference}
            onChange={setReference}
            placeholder="ADM-001"
            autoComplete="username" />
        </> :

        <>
            <TextField
            id="licence"
            label="Licence number"
            value={reference}
            onChange={setReference}
            placeholder="ATPL-SL-2291"
            autoComplete="username" />
          
          </>
        }

        <TextField
          id="password"
          label="Password"
          type="password"
          value={password}
          onChange={setPassword}
          placeholder="••••••••"
          autoComplete="current-password" />
        

        {error ?
        <p className="flex items-start gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-200" role="alert">
            <AlertTriangleIcon className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            {error}
          </p> :
        null}

        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-xs text-slate-400">
            <input
              type="checkbox"
              className="h-3.5 w-3.5 rounded border-line-strong bg-ink text-accent focus:ring-accent" />
            
            Keep me signed in
          </label>
          <button
            type="button"
            className="text-xs text-accent-pale underline-offset-4 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-accent">
            
            Forgot password?
          </button>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-accent px-4 py-3 text-sm font-bold text-white transition-colors hover:bg-sky-400 disabled:opacity-70 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-soft">
          
          <LogInIcon className="h-4 w-4" aria-hidden="true" />
          {submitting ? 'Verifying…' : `Sign in as ${roleMeta[role].label}`}
        </button>
      </form>
    </AuthShell>);

}