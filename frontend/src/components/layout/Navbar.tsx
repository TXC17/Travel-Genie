import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Sparkles, MapPin, Compass, Users, LogIn, User as UserIcon, LogOut, MessageSquare, LayoutDashboard } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { AuthModal } from '../auth/AuthModal';
import { ThemeToggle } from '../common/ThemeToggle';

export const Navbar: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [authModalOpen, setAuthModalOpen] = useState(false);

  const navLinks = [
    { name: 'Plan Trip', path: '/plan', icon: Compass },
    { name: 'AI Chat', path: '/chat', icon: MessageSquare },
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard, authOnly: true },
  ];

  return (
    <>
      <header className="sticky top-0 z-50 bg-slate-100/95 dark:bg-black/90 backdrop-blur-md border-b-2 border-slate-300/80 dark:border-neutral-800 shadow-sm transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand Logo */}
          <Link to="/" className="flex items-center space-x-2.5 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-emerald-500 dark:from-emerald-600 dark:to-amber-500 flex items-center justify-center text-white shadow-md shadow-emerald-600/20 dark:shadow-emerald-500/20 group-hover:scale-105 transition-transform">
              <Sparkles className="w-5 h-5 animate-pulse text-white dark:text-amber-100" />
            </div>
            <div>
              <span className="text-xl font-extrabold bg-gradient-to-r from-emerald-600 via-emerald-500 to-amber-500 dark:from-emerald-400 dark:via-emerald-300 dark:to-amber-300 bg-clip-text text-transparent">
                Travel Genie
              </span>
              <span className="hidden sm:inline-block ml-2 text-[10px] uppercase tracking-wider font-extrabold px-2 py-0.5 bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 rounded-full border border-emerald-200 dark:border-emerald-800/80">
                OR-Tools AI
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-6">
            {navLinks
              .filter((link) => !link.authOnly || isAuthenticated)
              .map((link) => (
                <Link
                  key={link.name}
                  to={link.path}
                  className={`flex items-center space-x-1.5 text-sm font-semibold transition-colors ${
                    location.pathname === link.path
                      ? 'text-emerald-600 dark:text-emerald-400 font-extrabold'
                      : 'text-slate-600 dark:text-neutral-300 hover:text-emerald-600 dark:hover:text-emerald-400'
                  }`}
                >
                  <link.icon className="w-4 h-4" />
                  <span>{link.name}</span>
                </Link>
              ))}
          </nav>

          {/* Actions: Theme Toggle & Auth CTA */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            {/* Prominent Theme Toggle */}
            <ThemeToggle />

            {isAuthenticated ? (
              <div className="flex items-center space-x-2 sm:space-x-3">
                <button
                  onClick={() => navigate('/dashboard')}
                  className="liquid-btn text-xs text-slate-700 dark:text-neutral-200 font-bold flex items-center gap-1.5 bg-slate-100 dark:bg-neutral-900 hover:bg-slate-200 dark:hover:bg-neutral-800 border border-slate-200 dark:border-neutral-800 px-3 py-1.5 rounded-xl cursor-pointer"
                >
                  <UserIcon className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <span>{user?.full_name?.split(' ')[0] || 'Traveler'}</span>
                </button>
                <button
                  onClick={logout}
                  className="liquid-btn p-2 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 cursor-pointer"
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setAuthModalOpen(true)}
                  className="liquid-btn inline-flex items-center space-x-1.5 px-3 py-2 text-xs font-bold text-slate-700 dark:text-neutral-300 hover:text-emerald-600 dark:hover:text-emerald-400 cursor-pointer"
                >
                  <LogIn className="w-4 h-4" />
                  <span>Sign In</span>
                </button>
                <Link
                  to="/plan"
                  className="liquid-btn inline-flex items-center space-x-1.5 px-3.5 sm:px-4 py-2 text-xs font-bold text-white dark:text-black bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-400 dark:hover:bg-emerald-300 rounded-xl shadow-sm shadow-emerald-600/20 dark:shadow-emerald-400/20 cursor-pointer"
                >
                  <span>Plan Trip</span>
                </Link>
              </div>
            )}
          </div>
        </div>
      </header>

      <AuthModal isOpen={authModalOpen} onClose={() => setAuthModalOpen(false)} />
    </>
  );
};
