/**
 * Axios HTTP Client configured with automatic JWT auth headers and error handling.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Request Interceptor: Attach JWT Token if present
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('travel_genie_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle auth expiration
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('travel_genie_token');
      localStorage.removeItem('travel_genie_user');
      // Could dispatch event or redirect if appropriate
    }
    return Promise.reject(error);
  }
);
