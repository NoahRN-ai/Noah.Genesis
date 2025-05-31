```typescript
import apiClient from './apiClient';
import { UserProfileData, UserProfileUpdatePayload } from '../types/api';

export const getUserProfile = async (userId: string): Promise<UserProfileData> => {
  try {
    const response = await apiClient.get<UserProfileData>(`/users/${userId}/profile`);
    return response.data;
  } catch (error: any) {
    console.error(`Error fetching profile for user ${userId}:`, error);
    const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch user profile.';
    throw new Error(errorMessage);
  }
};

export const updateUserProfile = async (
  userId: string,
  payload: UserProfileUpdatePayload
): Promise<UserProfileData> => {
  try {
    const response = await apiClient.put<UserProfileData>(`/users/${userId}/profile`, payload);
    return response.data;
  } catch (error: any) {
    console.error(`Error updating profile for user ${userId}:`, error);
    const errorMessage = error.response?.data?.detail || error.message || 'Failed to update user profile.';
    throw new Error(errorMessage);
  }
};
```
