import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, AuthState } from '../types';
import { authService, LoginPayload, RegisterPayload } from '../services/authService';

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    try {
      const storedToken = localStorage.getItem('travel_genie_token');
      const storedUser = localStorage.getItem('travel_genie_user');
      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      }
    } catch (e) {
      console.error('Failed to restore auth session:', e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const data = await authService.login({ email, password });
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('travel_genie_token', data.access_token);
    localStorage.setItem('travel_genie_user', JSON.stringify(data.user));
  };

  const register = async (email: string, password: string, fullName: string) => {
    const data = await authService.register({ email, password, full_name: fullName });
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('travel_genie_token', data.access_token);
    localStorage.setItem('travel_genie_user', JSON.stringify(data.user));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('travel_genie_token');
    localStorage.removeItem('travel_genie_user');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
