import React from 'react';

export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="mt-auto border-t border-line py-6 text-center text-sm text-slate-500">
      <div className="mx-auto flex max-w-[1800px] flex-col items-center justify-between gap-4 px-4 sm:flex-row sm:px-6 lg:px-8 xl:px-10">
        <p>
          &copy; {year} AI-Based Hyper-Local Aviation Weather Forecast Verification System for Sri Lankan Monsoon Patterns. All rights reserved.
        </p>
        <div className="flex gap-4 text-xs font-medium">
          <a href="#" className="hover:text-slate-300 transition-colors">Privacy Policy</a>
          <a href="#" className="hover:text-slate-300 transition-colors">Terms of Service</a>
          <a href="#" className="hover:text-slate-300 transition-colors">Documentation</a>
        </div>
      </div>
    </footer>
  );
}
