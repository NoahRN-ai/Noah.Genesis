import React from 'react';
import { Modal } from '@mantine/core';
import PatientDataForm from './PatientDataForm'; // Assuming it's in the same components folder

interface PatientDataLogModalProps {
  opened: boolean;
  onClose: () => void;
  patientId: string; // Allow patientId to be passed in, default to mock if needed by caller
}

const PatientDataLogModal: React.FC<PatientDataLogModalProps> = ({
  opened,
  onClose,
  patientId,
}) => {
  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="Log New Patient Data"
      size="lg" // Adjust size as needed
      padding="md"
    >
      <PatientDataForm patientId={patientId} />
    </Modal>
  );
};

export default PatientDataLogModal;
