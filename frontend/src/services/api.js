import axios from 'axios';
import authServices from './auth'

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

// HANDLE TOKEN REFRESH

// flag to stop concurrent refreshes
let isRefreshing = false

// An array to hold pending requests while token is being refreshed
let failedQueue = []


const processQueue = (token = null) => {
  // Iterated over promises from failed reqs 
  failedQueue.forEach((prom) => {
    if (token) {
      // If we got a new token, resolve the promise
      prom.resolve(token);
    }

    else {
      // Otherwise, reject the promise
      prom.reject();
    }

  })

  failedQueue = []; // Clear the queue
}

api.interceptors.response.use(
  (response) => response, // if no error, return response

  async (error) => {
    const originalReq = error.config // contains properties of the axios error e.g. url, headers

    // Check if the error status is 401 and we haven't already retried this request
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // If a refresh is already in progress, the current request is queued until the token is refreshed
      // Create a new promise to hold the retry until token refresh completes

      if (isRefreshing) {
        // The promise represents the future result of the token refresh op
        return new Promise(function (resolve, reject) {
          failedQueue.push({ resolve, reject });
        })

        // Triggered by promresolve in processQueue
        .then((token) => {
          // Update header with nee access token
          originalReq.headers.Authorization = `Bearer ${token}`;

          // retry request
          return api(originalReq);
        })

        .catch(() => Promise.reject(error))
      }

      // If not currently refreshing, set the flag and try refreshing
      isRefreshing = true

      try {
        const data = await authServices.refreshToken()
        const newAccessToken = data.access;


        // Store the new token in local storage
        localStorage.setItem('access', newAccessToken);


        // Process any queued requests waiting for the new token
        processQueue(newAccessToken);

        // Update original request with new token and retry
        return api(originalReq)
      }

      catch (refreshError) {
         // If refresh fails, process the queue with failure and clear tokens
         processQueue(null);
         localStorage.clear();

         window.location.href = "/login/"; // redirect user to login
         return Promise.reject(refreshError);
      }

      finally {
        // Reset refresh flag
        isRefreshing = false;
      }
    }

    // If the error is not due to authentication, simply reject it
    return Promise.reject(error);
  }
)