import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import type { AuthUser, Role } from '../types/auth';
import { roleMeta } from '../types/auth';

const API_BASE = 'http://localhost:8000';

type SignInInput = {
  role: Role;
  name: string;
  reference: string;
  password?: string;
  email?: string;
  organisation?: string;
  station?: string;
};

type AuthContextValue = {
  user: AuthUser | null;
  signIn: (input: SignInInput) => Promise<AuthUser>;
  signUp: (input: SignInInput) => Promise<AuthUser>;
  signOut: () => void;
  updateUser: (changes: Partial<AuthUser>) => Promise<void>;
  deactivateAccount: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function toInitials(name: string): string {
  if (!name) return 'UNK';
  const parts = name.replace(/\b(capt\.?|first officer|fo)\b/gi, '').trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return 'MET';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

export function AuthProvider({ children }: {children: React.ReactNode;}) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    try {
      const stored = localStorage.getItem('aviation_auth_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    if (user) {
      localStorage.setItem('aviation_auth_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('aviation_auth_user');
      localStorage.removeItem('aviation_auth_token');
    }
  }, [user]);

  const signIn = useCallback(async (input: SignInInput) => {
    try {
      const response = await axios.post(`${API_BASE}/auth/login`, {
        username: input.reference,
        password: input.password || "password123", // default fallback for now
        role: input.role
      });
      
      const data = response.data.user;
      const token = response.data.access_token;
      
      localStorage.setItem('aviation_auth_token', token);
      
      const nextUser: AuthUser = {
        name: data.name,
        initials: toInitials(data.name),
        role: data.role as Role,
        title: roleMeta[data.role as Role].title,
        reference: data.username,
        email: data.email || '',
        phone: '+94 11 245 2451', // Mock phone since it's not in DB
        organisation: data.organisation || '',
        station: data.station || ''
      };
      
      setUser(nextUser);
      return nextUser;
    } catch (error: any) {
      if (error.response && error.response.data) {
        throw new Error(error.response.data.detail || "Authentication failed");
      }
      throw new Error("Network error during login");
    }
  }, []);

  const signUp = useCallback(async (input: SignInInput) => {
    try {
      const response = await axios.post(`${API_BASE}/auth/register`, {
        username: input.reference,
        password: input.password,
        role: input.role,
        name: input.name,
        email: input.email,
        organisation: input.organisation,
        station: input.station
      });
      // After successful registration, log them in immediately
      return await signIn(input);
    } catch (error: any) {
      if (error.response && error.response.data) {
        throw new Error(error.response.data.detail || "Registration failed");
      }
      throw new Error("Network error during registration");
    }
  }, [signIn]);

  const signOut = useCallback(() => setUser(null), []);

  const updateUser = useCallback(async (changes: Partial<AuthUser>) => {
    try {
      const token = localStorage.getItem('aviation_auth_token');
      await axios.put(`${API_BASE}/auth/profile`, changes, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      setUser((current) => {
        if (!current) return current;
        const merged = { ...current, ...changes };
        return { ...merged, initials: changes.name ? toInitials(changes.name) : merged.initials };
      });
    } catch (error: any) {
      console.error('Profile update failed:', error);
      throw error;
    }
  }, []);

  const deactivateAccount = useCallback(async () => {
    try {
      const token = localStorage.getItem('aviation_auth_token');
      await axios.post(`${API_BASE}/auth/deactivate`, {}, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      signOut();
    } catch (error: any) {
      console.error('Account deactivation failed:', error);
      throw error;
    }
  }, [signOut]);

  const value = useMemo(() => ({ user, signIn, signUp, signOut, updateUser, deactivateAccount }), [user, signIn, signUp, signOut, updateUser, deactivateAccount]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside an AuthProvider');
  }
  return context;
}
