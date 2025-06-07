import React from 'react'; // Removed useState as it's now from React.useState
import { useForm } from '@mantine/form'; // zodResolver removed as per user code
// import { z } from 'zod'; // Zod removed as per user code
import {
  TextInput, Button, Stack, Select, Textarea, Group, LoadingOverlay,
  Alert, ThemeIcon, rem // Added ThemeIcon and rem
} from '@mantine/core';
import { DateTimePicker } from '@mantine/dates';
import { IconDeviceFloppy, IconAlertCircle } from '@tabler/icons-react'; // Removed unused icons
import { notifications } from '@mantine/notifications';

import { PatientDataLogCreatePayload, PatientDataLogDataType } from '../types/api'; // PatientDataLogDataType is now an enum
import { submitPatientDataLog } from '../services/patientDataApiService';
import { useAuth } from '../hooks/useAuth';

// Zod schema and PatientDataFormValues are removed as per user's provided code for this file.
// The user's code seems to rely on Mantine's built-in validation or a simplified validation approach.

interface PatientDataFormValues {
  timestamp: Date;
  data_type: PatientDataLogDataType | ''; // Allow empty for initial Select state
  source?: string;
  content_observation_notes?: string;
  content_symptom_description?: string;
  content_symptom_severity?: 'mild' | 'moderate' | 'severe' | '';
  content_llm_summary_text?: string;
  content_user_document_text?: string;
  content_nursing_note_draft_text?: string; // Added
  content_shift_handoff_draft_text?: string; // Added
  content_general_notes?: string;
}

interface PatientDataFormProps {
  targetPatientUserId: string;
  onSubmitSuccess?: () => void;
  onCancel?: () => void;
}

export const PatientDataForm: React.FC<PatientDataFormProps> = ({
  targetPatientUserId,
  onSubmitSuccess,
  onCancel,
}) => {
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [submitError, setSubmitError] = React.useState<string | null>(null);
  const { currentUser } = useAuth();

  const form = useForm<PatientDataFormValues>({
    initialValues: {
      timestamp: new Date(),
      data_type: '',
      source: 'Manual Entry',
      content_observation_notes: '',
      content_symptom_description: '',
      content_symptom_severity: '',
      content_llm_summary_text: '',
      content_user_document_text: '',
      content_nursing_note_draft_text: '',
      content_shift_handoff_draft_text: '',
      content_general_notes: '',
    },
    validate: (values) => {
        const errors: Record<string, string> = {};
        if (!values.timestamp) errors.timestamp = "Event timestamp is required";
        if (!values.data_type) errors.data_type = "Please select a data type";

        if (values.data_type === PatientDataLogDataType.OBSERVATION && !values.content_observation_notes?.trim()) {
            errors.content_observation_notes = "Observation notes are required.";
        }
        if (values.data_type === PatientDataLogDataType.SYMPTOM_REPORT && !values.content_symptom_description?.trim()) {
            errors.content_symptom_description = "Symptom description is required.";
        }
        if (values.data_type === PatientDataLogDataType.LLM_SUMMARY && !values.content_llm_summary_text?.trim()) {
            errors.content_llm_summary_text = "Summary text is required.";
        }
        if (values.data_type === PatientDataLogDataType.USER_DOCUMENT && !values.content_user_document_text?.trim()) {
            errors.content_user_document_text = "Document text is required.";
        }
        if (values.data_type === PatientDataLogDataType.NURSING_NOTE_DRAFT && !values.content_nursing_note_draft_text?.trim()) {
            errors.content_nursing_note_draft_text = "Nursing note draft text is required.";
        }
        if (values.data_type === PatientDataLogDataType.SHIFT_HANDOFF_DRAFT && !values.content_shift_handoff_draft_text?.trim()) {
            errors.content_shift_handoff_draft_text = "Shift handoff draft text is required.";
        }
        return errors;
    },
  });

  const handleSubmit = async (values: PatientDataFormValues) => {
    if (!currentUser) {
      notifications.show({ title: 'Error', message: 'You must be logged in to submit data.', color: 'noahRed' });
      return;
    }
    if (!values.data_type) {
        form.setFieldError('data_type', 'Please select a data type.');
        return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    let contentData: Record<string, any> = {};
    switch (values.data_type) {
      case PatientDataLogDataType.OBSERVATION:
        contentData = { notes: values.content_observation_notes };
        break;
      case PatientDataLogDataType.SYMPTOM_REPORT:
        contentData = {
            description: values.content_symptom_description,
            severity: values.content_symptom_severity || undefined
        };
        break;
      case PatientDataLogDataType.LLM_SUMMARY:
        contentData = { summary_text: values.content_llm_summary_text };
        break;
      case PatientDataLogDataType.USER_DOCUMENT:
         contentData = { document_text: values.content_user_document_text };
         break;
      case PatientDataLogDataType.NURSING_NOTE_DRAFT:
         contentData = { draft_text: values.content_nursing_note_draft_text };
         break;
      case PatientDataLogDataType.SHIFT_HANDOFF_DRAFT:
         contentData = { draft_text: values.content_shift_handoff_draft_text };
         break;
      default:
        // It's good practice to handle unexpected data_type values or have a fallback.
        // For now, we assume data_type is one of the handled enums due to form validation.
        // If content_general_notes is meant as a true fallback for *any* unhandled type,
        // that logic would go here, but current setup implies specific content per type.
        // If a general notes field is applicable across types, it should be added explicitly to relevant cases.
        contentData = { notes: values.content_general_notes }; // Fallback if general notes are used this way
    }

    const payload: PatientDataLogCreatePayload = {
      timestamp: values.timestamp.toISOString(),
      data_type: values.data_type as PatientDataLogDataType, // Validated by form
      content: contentData,
      source: values.source || "Manual Web Entry",
    };

    try {
      await submitPatientDataLog(targetPatientUserId, payload);
      notifications.show({
        title: 'Data Logged',
        message: `Data for type '${values.data_type}' has been successfully logged.`,
        color: 'noahGreen',
        icon: <IconDeviceFloppy />,
      });
      form.reset(); // Reset form to initial values
      if (onSubmitSuccess) {
        onSubmitSuccess();
      }
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to log data. Please try again.';
      setSubmitError(message);
      notifications.show({
        title: 'Submission Failed',
        message,
        color: 'noahRed',
        icon: <IconAlertCircle />,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const selectedDataType = form.values.data_type;

  // Prepare data for the Select component
  // Filter out enum keys that are numbers (reverse mapping) if any, then map to label/value
  const dataTypeOptions = Object.keys(PatientDataLogDataType)
    .filter(key => isNaN(Number(key))) // Ensure we only get string keys if it's a mixed enum (not typical for string enums)
    .map(key => ({
      value: PatientDataLogDataType[key as keyof typeof PatientDataLogDataType],
      label: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) // Improved label formatting
    }));

  return (
    // Paper shadow="none" p={0} was in user prompt, but might be better with some padding if used in modal directly
    // For consistency with other forms, let's use p="md" and withBorder if it's the main content of a modal
    <div style={{position: 'relative', minWidth: rem(300) }}> {/* Using div instead of Paper for direct style control */}
      <LoadingOverlay visible={isSubmitting} overlayProps={{ radius: "sm", blur: 2 }} />
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Stack gap="md">
          <DateTimePicker
            label="Timestamp of Event/Observation"
            placeholder="Pick date and time"
            required
            {...form.getInputProps('timestamp')}
            valueFormat="MMM DD, YYYY hh:mm A"
            maxDate={new Date()}
          />
          <Select
            label="Data Type"
            placeholder="Select the type of data you are logging"
            data={dataTypeOptions}
            required
            {...form.getInputProps('data_type')}
          />
          <TextInput
            label="Source (Optional)"
            placeholder="e.g., Patient Self-Report, Nurse Observation"
            {...form.getInputProps('source')}
          />

          {selectedDataType === PatientDataLogDataType.OBSERVATION && (
            <Textarea
              label="Observation Notes"
              placeholder="Enter detailed observations (e.g., vitals, patient condition)"
              autosize
              minRows={3}
              required
              {...form.getInputProps('content_observation_notes')}
            />
          )}
          {selectedDataType === PatientDataLogDataType.SYMPTOM_REPORT && (
            <>
              <Textarea
                label="Symptom Description"
                placeholder="Describe the symptoms experienced"
                autosize
                minRows={3}
                required
                {...form.getInputProps('content_symptom_description')}
              />
              <Select
                label="Symptom Severity (Optional)"
                placeholder="Select severity"
                data={[
                  { value: '', label: 'N/A' }, // Allow unsetting or not applicable
                  { value: 'mild', label: 'Mild' },
                  { value: 'moderate', label: 'Moderate' },
                  { value: 'severe', label: 'Severe' },
                ]}
                {...form.getInputProps('content_symptom_severity')}
              />
            </>
          )}
          {selectedDataType === PatientDataLogDataType.LLM_SUMMARY && (
             <Textarea
              label="LLM Summary Text"
              placeholder="Enter or paste LLM summary content"
              autosize
              minRows={4}
              required
              {...form.getInputProps('content_llm_summary_text')}
            />
          )}
          {selectedDataType === PatientDataLogDataType.USER_DOCUMENT && (
             <Textarea
              label="Document Text"
              placeholder="Paste or type text content of a user document"
              autosize
              minRows={5}
              required
              {...form.getInputProps('content_user_document_text')}
            />
          )}
          {selectedDataType === PatientDataLogDataType.NURSING_NOTE_DRAFT && (
             <Textarea
              label="Nursing Note Draft"
              placeholder="Draft content for a nursing note"
              autosize
              minRows={4}
              required
              {...form.getInputProps('content_nursing_note_draft_text')}
            />
          )}
          {selectedDataType === PatientDataLogDataType.SHIFT_HANDOFF_DRAFT && (
             <Textarea
              label="Shift Handoff Draft"
              placeholder="Draft content for a shift handoff report"
              autosize
              minRows={4}
              required
              {...form.getInputProps('content_shift_handoff_draft_text')}
            />
          )}
          {/* Fallback general notes - consider if this is needed if all types have specific fields */}
          {/* Or if it's a common field for *all* types in addition to specific ones */}
          {/* Based on current structure, it seems like a fallback if no other fields match, which is less likely with enum. */}
          {/* If it's an *additional* note, it should be available always or tied to specific types. */}
          {/* For now, let's assume it's for types not explicitly handled by other fields: */}
          {![
                PatientDataLogDataType.OBSERVATION,
                PatientDataLogDataType.SYMPTOM_REPORT,
                PatientDataLogDataType.LLM_SUMMARY,
                PatientDataLogDataType.USER_DOCUMENT,
                PatientDataLogDataType.NURSING_NOTE_DRAFT,
                PatientDataLogDataType.SHIFT_HANDOFF_DRAFT
            ].includes(selectedDataType as PatientDataLogDataType) && selectedDataType && (
             <Textarea
                label="General Notes / Content"
                placeholder="Enter details for this log entry"
                autosize
                minRows={3}
                {...form.getInputProps('content_general_notes')}
             />
           )}

          {submitError && (
            <Alert title="Error" color="noahRed" icon={<IconAlertCircle size="1rem" />} withCloseButton onClose={() => setSubmitError(null)} radius="md">
              {submitError}
            </Alert>
          )}
          <Group justify="flex-end" mt="lg">
            {onCancel && <Button variant="default" onClick={onCancel} disabled={isSubmitting}>Cancel</Button>}
            <Button
              type="submit"
              leftSection={<IconDeviceFloppy size="1rem" />}
              loading={isSubmitting}
              disabled={!form.values.data_type || isSubmitting} // Disable if no data_type or submitting
            >
              Log Data
            </Button>
          </Group>
        </Stack>
      </form>
    </div>
  );
};
