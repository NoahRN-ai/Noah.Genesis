import React from 'react';
import { Container, Title } from '@mantine/core';
import PatientDataForm from '../components/PatientDataForm';

const PatientDataLogPage: React.FC = () => {
  // Mock patientId as per requirement
  const mockPatientId = "patient-123";

  return (
    <Container size="md" mt="xl">
      <Title order={1} align="center" mb="xl">
        Log Patient Data
      </Title>
      <PatientDataForm patientId={mockPatientId} />
    </Container>
  );
};

export default PatientDataLogPage;
