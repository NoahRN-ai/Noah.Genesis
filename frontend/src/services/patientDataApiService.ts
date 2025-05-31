```typescript
import apiClient from './apiClient';
import { PatientDataLogCreatePayload, PatientDataLogData } from '../types/api';

interface GetPatientDataLogsParams {
  patientUserId: string;
  limit?: number;
  orderBy?: string;
  descending?: boolean;
}

export const submitPatientDataLog = async (
  targetPatientUserId: string,
  payload: PatientDataLogCreatePayload
): Promise<PatientDataLogData> => {
  try {
    const response = await apiClient.post<PatientDataLogData>(
      `/patient-data-logs`, // target_patient_user_id moved to query params by backend spec for POST
      payload,
      { params: { target_patient_user_id: targetPatientUserId } }
    );
    return response.data;
  } catch (error: any) {
    console.error('Error submitting patient data log:', error);
    const errorMessage = error.response?.data?.detail || error.message || 'Failed to submit patient data log.';
    throw new Error(errorMessage);
  }
};

export const getPatientDataLogs = async ({
  patientUserId,
  limit,
  orderBy,
  descending,
}: GetPatientDataLogsParams): Promise<PatientDataLogData[]> => {
  try {
    const response = await apiClient.get<PatientDataLogData[]>(
      '/patient-data-logs',
      {
        params: {
          patient_user_id: patientUserId,
          limit,
          order_by: orderBy,
          descending,
        },
      }
    );
    return response.data;
  } catch (error: any) {
    console.error(`Error fetching patient data logs for user ${patientUserId}:`, error);
    const errorMessage = error.response?.data?.detail || error.message || 'Failed to fetch patient data logs.';
    throw new Error(errorMessage);
  }
};
```
