import React from 'react';
import { Paper, Title, Text, Stack, Alert, Loader, Center, Group } from '@mantine/core'; // Added Group
import { IconFileInfo, IconNotes, IconAlertCircle } from '@tabler/icons-react'; // Added IconAlertCircle

interface PatientSummaryDisplayProps {
  summaryContent?: string | null;
  isLoading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
}

export const PatientSummaryDisplay: React.FC<PatientSummaryDisplayProps> = ({
  summaryContent,
  isLoading,
  error,
  // onRefresh, // onRefresh was in the provided code but not used in the JSX, so commented out for now
}) => {
  return (
    <Paper shadow="xs" p="md" withBorder radius="md">
      <Stack>
        <Group justify="space-between">
            <Title order={4} ff={'Greycliff CF, sans-serif'}>Patient Summary</Title>
            {/* Optional: Add a refresh button or other actions here */}
            {/* {onRefresh && <Button onClick={onRefresh} variant="light" size="xs" leftIcon={<IconReload size="0.9rem"/>}>Refresh</Button>} */}
        </Group>

        {isLoading && (
          <Center py="lg">
            <Loader />
            <Text ml="sm" c="dimmed">Loading summary...</Text>
          </Center>
        )}

        {error && !isLoading && (
          <Alert title="Error" color="noahRed" icon={<IconAlertCircle size="1rem" />}>
            Could not load patient summary: {error}
          </Alert>
        )}

        {!isLoading && !error && summaryContent && (
          // Using Paper for themed background and consistent padding/radius
          <Paper p="sm" radius="sm" bg="var(--mantine-color-noahDarkGray-0)" style={{whiteSpace: 'pre-wrap', maxHeight: '300px', overflowY: 'auto'}}>
            <Text component="div" lh={1.6} size="sm">{summaryContent}</Text>
          </Paper>
        )}

        {!isLoading && !error && !summaryContent && (
          <Center py="lg">
            <Stack align="center" gap="xs">
                <IconNotes size="2.5rem" stroke={1.5} color="var(--mantine-color-noahDarkGray-4)" />
                <Text c="dimmed" ta="center">
                    No summary available at the moment. <br/>
                    Noah.AI can generate summaries based on logged patient data.
                </Text>
            </Stack>
          </Center>
        )}
      </Stack>
    </Paper>
  );
};
