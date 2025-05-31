```typescript
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { authInstance, getIdToken, User } from './firebaseService';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000, // 15 seconds timeout
});

// Request interceptor to add the Firebase ID token
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const user: User | null = authInstance.currentUser;
    if (user) {
      try {
        // It's generally better to get a fresh token, or one that's not significantly old.
        // Firebase SDK handles caching, but forceRefresh=true can be used if issues.
        // For most requests, just getting the current token is fine.
        const idToken = await getIdToken(user /*, forceRefreshIfNeeded */);
        if (idToken) {
          config.headers.Authorization = `Bearer ${idToken}`;
        }
      } catch (error) {
        console.error('apiClient: Error getting ID token for API request:', error);
        // Don't proceed with request if token is essential and fails to retrieve
        return Promise.reject(new Error('Failed to retrieve authentication token.'));
      }
    }
    // If no user, request proceeds without Authorization header (backend will deny if protected)
    return config;
  },
  (error: AxiosError) => {
    console.error('apiClient: Request error in interceptor:', error);
    return Promise.reject(error);
  }
);

// Response interceptor (Optional - for global error handling like 401)
// This is complex because you can't use React hooks (like useAuth) inside interceptors directly.
// A more advanced setup would involve an event bus or a way to trigger AuthContext's signOut/refresh.
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      console.warn('apiClient: Received 401. User may need to re-authenticate or token expired.');
      // At this point, if you have a global event bus or a way to trigger sign out from AuthContext,
      // you could dispatch an event here. For now, we rely on components handling 401s
      // by checking currentUser in AuthContext or catching specific API errors.
      // Example: window.dispatchEvent(new Event('auth-error-401'));
      // firebaseSignOut(authInstance); // Forcing a sign out, onAuthStateChanged in AuthContext will pick it up.
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```
