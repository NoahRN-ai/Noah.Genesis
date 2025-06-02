```tsx
import React, { useState, useEffect } from 'react';
import { Container, Alert, Loader, Center } from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';
import { ChatInterface } from '../components/ChatInterface';
import { useAuth } from '../hooks/useAuth';
// import { getSessionHistory } from '../services/historyApiService'; // Deferred for MVP core
import { DisplayMessage, InteractionOutputData } from '../types/api';
import { v4 as uuidv4 } from 'uuid';

const ChatPage: React.FC = () => {
  const { currentUser, isLoading: authIsLoading, isInitialized } = useAuth();

  const [sessionId] = useState<string>(() => uuidv4());
  const [initialMessages] = useState<DisplayMessage[]>([]); // No history loading for MVP start of page
  const [pageError, setPageError] = useState<string | null>(null);


  if (authIsLoading || !isInitialized) { // Check both flags from AuthContext
    return (
      <Center style={{ height: 'calc(100vh - var(--app-shell-header-height, 60px))' }}>
        <Loader size="xl" />
      </Center>
    );
  }

  if (!currentUser) {
    // This should be caught by ProtectedRoute.
    // If reached, it means ProtectedRoute might not be working or this page is accessed outside its scope.
    // For robustness, one might redirect or show an error. But ProtectedRoute is the primary guard.
    console.error("ChatPage accessed without current user, ProtectedRoute should have handled this.");
    return (
        <Container pt="xl">
            <Alert title="Authentication Required" color="noahRed" icon={<IconAlertCircle />}>
                Please log in to access the chat with Noah.AI. This page requires authentication.
            </Alert>
        </Container>
    );
  }

  return (
    <Container
      fluid
      p={0}
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - var(--app-shell-header-height, 60px))',
        overflow: 'hidden'
      }}
    >
      {pageError && (
        <Alert
          icon={<IconAlertCircle size="1rem" />}
          title="Page Error"
          color="noahRed"
          withCloseButton
          onClose={() => setPageError(null)}
          m="md"
          radius="md"
        >
          {pageError}
        </Alert>
      )}

      <ChatInterface
        key={sessionId} // Re-mount ChatInterface if sessionId changes, ensuring fresh state.
        initialMessages={initialMessages} // For MVP, usually starts empty. Future: load history here.
        currentUserId={currentUser.uid}
        initialSessionId={sessionId}
      />
    </Container>
  );
};

export default ChatPage;
```
