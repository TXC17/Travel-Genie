import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { Footer } from './Footer';

export const Layout: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-slate-200/95 dark:bg-black text-slate-900 dark:text-neutral-100 transition-colors duration-200 selection:bg-emerald-500 selection:text-white relative overflow-hidden">
      {/* Ambient background vibrant light gradients for Light Mode (hidden in pitch black dark mode) */}
      <div className="fixed -top-40 -left-40 w-[600px] h-[600px] bg-gradient-to-br from-emerald-300/60 via-teal-300/40 to-transparent rounded-full blur-3xl pointer-events-none -z-10 dark:hidden" />
      <div className="fixed top-1/3 -right-40 w-[650px] h-[650px] bg-gradient-to-tl from-teal-300/55 via-emerald-200/45 to-transparent rounded-full blur-3xl pointer-events-none -z-10 dark:hidden" />
      <div className="fixed -bottom-40 left-1/4 w-[550px] h-[550px] bg-gradient-to-tr from-amber-300/50 via-emerald-200/40 to-transparent rounded-full blur-3xl pointer-events-none -z-10 dark:hidden" />
      <div className="fixed top-2/3 left-10 w-[400px] h-[400px] bg-gradient-to-br from-cyan-200/40 via-emerald-200/35 to-transparent rounded-full blur-3xl pointer-events-none -z-10 dark:hidden" />

      <Navbar />
      <main className="flex-grow">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};
