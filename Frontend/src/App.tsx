import React from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { RequireAuth } from './components/auth/RequireAuth';
import { AppLayout } from './components/layout/AppLayout';
import { Dashboard } from './pages/Dashboard';
import { WeatherForecasting } from './pages/WeatherForecasting';
import { ForecastMaps } from './pages/ForecastMaps';
import { ActivityLogs } from './pages/ActivityLogs';
import { PlaceholderPage } from './pages/PlaceholderPage';
import { Profile } from './pages/Profile';
import { Settings } from './pages/Settings';
import { SignIn } from './pages/SignIn';
import { SignUp } from './pages/SignUp';
import { PilotDashboard } from './pages/pilot/PilotDashboard';
import { FlightPlanning } from './pages/pilot/FlightPlanning';
import { BriefingReview } from './pages/pilot/BriefingReview';
import { RouteMaps } from './pages/pilot/RouteMaps';
import { Documents } from './pages/pilot/Documents';
import { RecentFlightPlans } from './pages/pilot/RecentFlightPlans';

export function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/sign-in" element={<SignIn />} />
            <Route path="/sign-up" element={<SignUp />} />
            <Route
              element={
              <RequireAuth>
                  <AppLayout />
                </RequireAuth>
              }>
              
              <Route
                index
                element={
                <RequireAuth allow={['forecaster']}>
                    <Dashboard />
                  </RequireAuth>
                } />
              
              <Route
                path="/forecasting"
                element={
                <RequireAuth allow={['forecaster']}>
                    <WeatherForecasting />
                  </RequireAuth>
                } />
              
              <Route
                path="/maps"
                element={
                <RequireAuth allow={['forecaster']}>
                    <ForecastMaps />
                  </RequireAuth>
                } />
              
              <Route
                path="/logs"
                element={
                <RequireAuth allow={['forecaster', 'pilot']}>
                    <ActivityLogs />
                  </RequireAuth>
                } />
              

              <Route
                path="/pilot"
                element={
                <RequireAuth allow={['pilot']}>
                    <PilotDashboard />
                  </RequireAuth>
                } />
              
              <Route
                path="/pilot/flight-planning"
                element={
                <RequireAuth allow={['pilot']}>
                    <FlightPlanning />
                  </RequireAuth>
                } />
              
              <Route
                path="/pilot/briefing"
                element={
                <RequireAuth allow={['pilot']}>
                    <BriefingReview />
                  </RequireAuth>
                } />
              
              <Route
                path="/pilot/maps"
                element={
                <RequireAuth allow={['pilot']}>
                    <RouteMaps />
                  </RequireAuth>
                } />
              
              <Route
                path="/pilot/documents"
                element={
                <RequireAuth allow={['pilot']}>
                    <Documents />
                  </RequireAuth>
                } />
              
              <Route
                path="/pilot/recent-plans"
                element={
                <RequireAuth allow={['pilot']}>
                    <RecentFlightPlans />
                  </RequireAuth>
                } />
              

              <Route path="/profile" element={<Profile />} />
              <Route path="/settings" element={<Settings />} />
              <Route
                path="*"
                element={
                <PlaceholderPage
                  title="Page not found"
                  description="The requested console view does not exist." />

                } />
              
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>);

}