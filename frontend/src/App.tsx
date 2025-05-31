```tsx
import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Center, Loader, Box } from '@mantine/core'; // Added Box

import { AppLayout } from './components/common/Layout';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import LoginPage from './pages/LoginPage'; // Eager load

const ChatPage = lazy(() => import('./pages/ChatPage'));
const UserProfilePage = lazy(() => import('./pages/UserProfilePage'));
const PatientDataLogPage = lazy(() => import('./pages/PatientDataLogPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));

const LoadingFallback = () => (
  <Box style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexGrow: 1, height: 'calc(100vh - 60px)' }}> {/* Assuming header height of 60px */}
    <Loader size="xl" />
  </Box>
);

function App() {
  return (
    <AppLayout>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/profile/:userId" element={<UserProfilePage />} />
            <Route path="/patient-data" element={<PatientDataLogPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/" element={<Navigate to="/chat" replace />} />
          </Route>

          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </AppLayout>
  );
}

export default App;
```
