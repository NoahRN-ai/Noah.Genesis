```typescript
import apiClient from './apiClient';
import { SessionHistoryResponsePayload } from '../types/api';

interface GetSessionHistoryParams {
  sessionId: string;
  limit?: number;
}

export const getSessionHistory = async ({
  sessionId,
  limit,
}: GetSessionHistoryParams): Promise<SessionHistoryResponsePayload> => {
  try {
    const response = await apiClient.get<SessionHistoryResponsePayload>(
      `/sessions/${sessionId}/history`,
      {
        params: { limit },
      }
    );
    return response.data;
  } catch (error: any) {
    console.error(`Error fetching history for session ${sessionId}:`, error);
    const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch session history.';
    throw new Error(errorMessage);
  }
};
```
