import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL, // URL for API Requests
  timeout: parseInt(import.meta.env.VITE_API_TIMEOUT), // Max response wait time
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to requests
// Request Interceptor runs before the request is sent
// The config object contains the configuration for the request (URL, headers, data, etc.)

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access'); // Get access token from local storage
  if (token) {
    config.headers.Authorization = `Bearer ${token}`; // If token exists add an Authorization header to the request. 
  }
  return config; // The interceptor must return the modified config object.  
});

// If you config not returned, the request won't be sent.