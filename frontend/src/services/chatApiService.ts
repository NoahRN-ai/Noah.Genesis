```typescript
import apiClient from './apiClient';
import { ChatRequestPayload, ChatResponsePayload } from '../types/api';

export const sendChatMessage = async (payload: ChatRequestPayload): Promise<ChatResponsePayload> => {
  try {
    const response = await apiClient.post<ChatResponsePayload>('/chat', payload);
    return response.data;
  } catch (error: any) { // Better to type as AxiosError if using axios explicitly
    console.error('Error sending chat message via chatApiService:', error);

    let errorMessage = 'Failed to get a response from Noah.AI. Please check your connection and try again.';
    if (error.response) {
      // Backend sent an error response
      const detail = error.response.data?.detail;
      if (typeof detail === 'string') {
        errorMessage = detail;
      } else if (error.response.statusText) {
        errorMessage = `Error ${error.response.status}: ${error.response.statusText}`;
      }
    } else if (error.request) {
      // Request was made but no response received
      errorMessage = 'No response received from Noah.AI. The service might be temporarily unavailable.';
    } else {
      // Something else happened in setting up the request
      if (error.message) {
        errorMessage = error.message;
      }
    }

    // In a production app, you might log this error to an external service:
    // Sentry.captureException(error, { extra: { payload } });

    throw new Error(errorMessage); // Re-throw a more user-friendly or specific error message
  }
};
```
