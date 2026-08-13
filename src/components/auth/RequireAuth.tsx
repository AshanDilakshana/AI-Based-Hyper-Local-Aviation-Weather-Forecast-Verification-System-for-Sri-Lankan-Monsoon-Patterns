import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import type { Role } from '../../types/auth';
import { roleMeta } from '../../types/auth';

type RequireAuthProps = {
  children: React.ReactNode;
  allow?: Role[];
};

export function RequireAuth({ children, allow }: RequireAuthProps) {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/sign-in" replace state={{ from: location.pathname }} />;
  }

  if (allow && !allow.includes(user.role)) {
    return <Navigate to={roleMeta[user.role].home} replace />;
  }

  return <>{children}</>;
}