import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import type { AuthUser, Role } from '../types/auth';
import { roleMeta } from '../types/auth';

type SignInInput = {
  role: Role;
  name: string;
  reference: string;
  email?: string;
  organisation?: string;
  station?: string;
};

type AuthContextValue = {
  user: AuthUser | null;
  signIn: (input: SignInInput) => AuthUser;
  signOut: () => void;
  updateUser: (changes: Partial<AuthUser>) => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function toInitials(name: string): string {
  const parts = name.replace(/\b(capt\.?|first officer|fo)\b/gi, '').trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return 'MET';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

export function AuthProvider({ children }: {children: React.ReactNode;}) {
  const [user, setUser] = useState<AuthUser | null>(null);

  const signIn = useCallback((input: SignInInput) => {
    const isPilot = input.role === 'pilot';
    const resolvedName = input.name.trim() || (isPilot ? 'Capt. N. Fernando' : 'A. Ranasinghe');
    const nextUser: AuthUser = {
      name: resolvedName,
      initials: toInitials(resolvedName),
      role: input.role,
      title: roleMeta[input.role].title,
      reference: input.reference.trim(),
      email: input.email?.trim() || (isPilot ? 'crew@operator.lk' : 'officer@meteo.gov.lk'),
      phone: '+94 11 245 2451',
      organisation: input.organisation?.trim() || (isPilot ? 'SriLankan Airlines' : 'Department of Meteorology'),
      station: input.station?.trim() || 'VCBI · Bandaranaike Intl.'
    };
    setUser(nextUser);
    return nextUser;
  }, []);

  const signOut = useCallback(() => setUser(null), []);

  const updateUser = useCallback((changes: Partial<AuthUser>) => {
    setUser((current) => {
      if (!current) return current;
      const merged = { ...current, ...changes };
      return { ...merged, initials: changes.name ? toInitials(changes.name) : merged.initials };
    });
  }, []);

  const value = useMemo(() => ({ user, signIn, signOut, updateUser }), [user, signIn, signOut, updateUser]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside an AuthProvider');
  }
  return context;
}