import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Layout } from './components/layout/Layout';
import { LandingPage } from './pages/LandingPage';
import { TripPlannerPage } from './pages/TripPlannerPage';
import { ItineraryPage } from './pages/ItineraryPage';
import { ChatPage } from './pages/ChatPage';
import { DashboardPage } from './pages/DashboardPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { ProtectedRoute } from './components/common/ProtectedRoute';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<LandingPage />} />
            <Route path="plan" element={<TripPlannerPage />} />
            <Route path="itinerary/:id" element={<ItineraryPage />} />
            <Route path="itinerary" element={<ItineraryPage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route
              path="dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
