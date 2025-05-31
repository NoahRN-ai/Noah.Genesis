```typescript
import apiClient from './apiClient';
import { ChatRequestPayload, ChatResponsePayload } from '../types/api';

export const sendChatMessage = async (payload: ChatRequestPayload): Promise<ChatResponsePayload> => {
  try {
    const response = await apiClient.post<ChatResponsePayload>('/chat', payload);
    return response.data;
  } catch (error: any) {
    console.error('Error sending chat message:', error);
    const errorMessage = error.response?.data?.detail || error.message || 'Failed to send chat message.';
    throw new Error(errorMessage);
  }
};
```
