import React from 'react';
import { Link } from 'react-router-dom';
import { Compass, Home } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="text-center space-y-5 max-w-md">
        <div className="w-16 h-16 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mx-auto shadow-sm">
          <Compass className="w-8 h-8 animate-spin" />
        </div>
        <h1 className="text-4xl font-extrabold text-slate-900">404</h1>
        <h2 className="text-xl font-bold text-slate-800">Destination Not Found</h2>
        <p className="text-sm text-slate-600">
          The page you are looking for does not exist or has been relocated in the itinerary.
        </p>
        <Link
          to="/"
          className="inline-flex items-center space-x-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors"
        >
          <Home className="w-4 h-4" />
          <span>Return Home</span>
        </Link>
      </div>
    </div>
  );
};
