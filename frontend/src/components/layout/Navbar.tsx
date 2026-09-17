import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Sparkles, MapPin, Compass, Users, LogIn, User as UserIcon, LogOut, MessageSquare, LayoutDashboard } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { AuthModal } from '../auth/AuthModal';

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
      <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand Logo */}
          <Link to="/" className="flex items-center space-x-2 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-700 to-teal-500 flex items-center justify-center text-white shadow-md shadow-teal-600/20 group-hover:scale-105 transition-transform">
              <Sparkles className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <span className="text-xl font-extrabold bg-gradient-to-r from-teal-800 to-teal-600 bg-clip-text text-transparent">
                Travel Genie
              </span>
              <span className="hidden sm:inline-block ml-2 text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 bg-teal-50 text-teal-700 rounded-full border border-teal-200">
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
                      ? 'text-teal-600 font-bold'
                      : 'text-slate-600 hover:text-teal-600'
                  }`}
                >
                  <link.icon className="w-4 h-4" />
                  <span>{link.name}</span>
                </Link>
              ))}
          </nav>

          {/* Auth CTA Actions */}
          <div className="flex items-center space-x-3">
            {isAuthenticated ? (
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => navigate('/dashboard')}
                  className="text-xs text-slate-700 font-bold flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-xl transition-all cursor-pointer"
                >
                  <UserIcon className="w-4 h-4 text-teal-600" />
                  <span>{user?.full_name?.split(' ')[0] || 'Traveler'}</span>
                </button>
                <button
                  onClick={logout}
                  className="p-2 text-slate-400 hover:text-rose-600 transition-colors cursor-pointer"
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setAuthModalOpen(true)}
                  className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-bold text-slate-700 hover:text-teal-600 transition-colors cursor-pointer"
                >
                  <LogIn className="w-4 h-4" />
                  <span>Sign In</span>
                </button>
                <Link
                  to="/plan"
                  className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 rounded-xl shadow-sm shadow-teal-600/20 transition-all hover:shadow cursor-pointer"
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
