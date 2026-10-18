import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { Footer } from './Footer';

export function AppLayout() {
  const [navOpen, setNavOpen] = useState(false);

  return (
    <div className="flex min-h-screen w-full bg-canvas font-sans text-slate-200 relative overflow-x-hidden">
      {/* Saga-Style Ambient Atmospheric Light Orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden z-0">
        <div className="absolute top-[-10%] right-[10%] h-[550px] w-[550px] rounded-full bg-accent/5 blur-[120px] animate-ambient-float" />
        <div className="absolute top-[40%] left-[-8%] h-[600px] w-[600px] rounded-full bg-sky-500/5 blur-[140px] animate-ambient-float-delayed" />
        <div className="absolute bottom-[-10%] right-[20%] h-[500px] w-[500px] rounded-full bg-amber-500/5 blur-[120px] animate-ambient-pulse" />
      </div>

      <Sidebar open={navOpen} onClose={() => setNavOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col relative z-10 lg:pl-72">
        <TopBar onMenuClick={() => setNavOpen(true)} />
        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8 xl:px-10">
          <div className="mx-auto w-full max-w-[1800px]">
            <Outlet />
          </div>
        </main>
        <Footer />
      </div>
    </div>
  );
}