import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AlertTriangleIcon, UserPlusIcon } from 'lucide-react';
import { AuthShell } from '../components/auth/AuthShell';
import { RoleSelector } from '../components/auth/RoleSelector';
import { TextField } from '../components/auth/TextField';
import { useAuth } from '../contexts/AuthContext';
import type { Role } from '../types/auth';
import { roleMeta } from '../types/auth';

export function SignUp() {
  const [role, setRole] = useState<Role>('forecaster');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [reference, setReference] = useState('');
  const [organisation, setOrganisation] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const { signIn } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }
    setError('');
    setSubmitting(true);
    window.setTimeout(() => {
      signIn({ role, name, reference, email, organisation });
      setSubmitting(false);
      navigate(roleMeta[role].home, { replace: true });
    }, 700);
  };

  return (
    <AuthShell
      eyebrow="Access request"
      title="Create a console account"
      description="Accounts are provisioned separately for forecasters and flight crew."
      footer={
      <>
          Already have credentials?{' '}
          <Link
          to="/sign-in"
          className="font-semibold text-accent-pale underline-offset-4 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-accent">
          
            Sign in
          </Link>
        </>
      }>
      
      <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
        <RoleSelector value={role} onChange={setRole} />

        <TextField
          id="name"
          label="Full name"
          value={name}
          onChange={setName}
          placeholder={role === 'pilot' ? 'Capt. N. Fernando' : 'A. Ranasinghe'}
          autoComplete="name" />
        

        <TextField
          id="email"
          label="Official email"
          type="email"
          value={email}
          onChange={setEmail}
          placeholder={role === 'pilot' ? 'crew@operator.lk' : 'officer@meteo.gov.lk'}
          autoComplete="email" />
        

        {role === 'forecaster' ?
        <TextField
          id="metId"
          label="Met Officer ID"
          value={reference}
          onChange={setReference}
          placeholder="MET-04821"
          hint="Verified against the Department of Meteorology roster." /> :


        <>
            <TextField
            id="licence"
            label="Licence number"
            value={reference}
            onChange={setReference}
            placeholder="ATPL-SL-2291" />
          
            <TextField
            id="operator"
            label="Airline / operator"
            value={organisation}
            onChange={setOrganisation}
            placeholder="SriLankan Airlines" />
          
          </>
        }

        <div className="grid gap-5 sm:grid-cols-2">
          <TextField
            id="password"
            label="Password"
            type="password"
            value={password}
            onChange={setPassword}
            placeholder="••••••••"
            autoComplete="new-password" />
          
          <TextField
            id="confirm"
            label="Confirm password"
            type="password"
            value={confirm}
            onChange={setConfirm}
            placeholder="••••••••"
            autoComplete="new-password" />
          
        </div>

        {error ?
        <p className="flex items-start gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-200" role="alert">
            <AlertTriangleIcon className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            {error}
          </p> :
        null}

        <button
          type="submit"
          disabled={submitting}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-accent px-4 py-3 text-sm font-bold text-white transition-colors hover:bg-sky-400 disabled:opacity-70 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-soft">
          
          <UserPlusIcon className="h-4 w-4" aria-hidden="true" />
          {submitting ? 'Submitting…' : `Create ${roleMeta[role].label} account`}
        </button>
        <p className="text-[11px] leading-relaxed text-slate-500">
          Requests are reviewed by the duty supervisor. Forecaster accounts gain model-run and publishing
          rights; pilot accounts are read-only for observations and charts.
        </p>
      </form>
    </AuthShell>);

}