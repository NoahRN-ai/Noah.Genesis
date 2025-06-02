```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';

import App from './App';
import { AuthProvider } from './contexts/AuthContext';
import { noahTheme } from './styles/theme'; // Import the refined Noah theme

// Core Mantine styles (MUST be imported before custom App styles)
import '@mantine/core/styles.css';
// Mantine notifications styles
import '@mantine/notifications/styles.css';
// Your custom global styles (if any, e.g., src/styles/global.css)
// import './styles/global.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <MantineProvider theme={noahTheme} defaultColorScheme="light" withGlobalStyles withNormalizeCSS>
      <Notifications position="top-right" zIndex={2077} autoClose={5000} />
      <BrowserRouter>
        <AuthProvider> {/* AuthProvider wraps App to provide auth context */}
          <App />
        </AuthProvider>
      </BrowserRouter>
    </MantineProvider>
  </React.StrictMode>
);
```
