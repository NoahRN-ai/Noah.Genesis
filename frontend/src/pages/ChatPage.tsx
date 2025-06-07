// In frontend/src/pages/ChatPage.tsx
import React, { useEffect, useState, useMemo } from 'react'; // Added useMemo
import { useParams, Navigate } from 'react-router-dom';
import { Container, Alert, Center, Loader, Accordion, ActionIcon, Tooltip, Box, Group, Button } from '@mantine/core'; // Added Accordion, ActionIcon, Tooltip, Box, Group, Button
import { IconAlertCircle, IconMessageChatbot, IconNotes, IconRefresh } from '@tabler/icons-react'; // Added IconNotes, IconRefresh
import { v4 as uuidv4 } from 'uuid';

import { useAuth } from '../hooks/useAuth';
import { ChatInterface } from '../components/ChatInterface';
import { InteractionOutputData, DisplayMessage } from '../types/api'; // InteractionOutputData might not be used if history formatting is simple
import { getSessionHistory } from '../services/historyApiService';
// Ensure PatientSummaryDisplay is imported as a named export
import { PatientSummaryDisplay } from '../components/PatientSummaryDisplay';
import { PatientDataLogModal } from '../components/PatientDataLogModal'; // For the button if modal is also here
import { useDisclosure } from '@mantine/hooks'; // For the modal button on this page

const ChatPage: React.FC = () => {
  const { currentUser, isLoading: authLoading, isInitialized } = useAuth();
  const { sessionId: sessionIdFromParams } = useParams<{ sessionId?: string }>();

  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [initialMessages, setInitialMessages] = useState<DisplayMessage[]>([]);
  const [pageError, setPageError] = useState<string | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false); // Retained if history loading is implemented

  // State for PatientSummaryDisplay
  const [summaryContent, setSummaryContent] = useState<string | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  // Disclosure for PatientDataLogModal if triggered from this page
  const [logDataModalOpened, { open: openLogDataModal, close: closeLogDataModal }] = useDisclosure(false);


  useEffect(() => {
    if (!isInitialized || authLoading) return;
    if (!currentUser) return; // Should be handled by ProtectedRoute

    const newSessionId = sessionIdFromParams || uuidv4();
    setCurrentSessionId(newSessionId);
    setInitialMessages([]); // Reset messages for new session logic

    if (sessionIdFromParams) {
      // TODO: Future - Fetch existing session history if sessionIdFromParams is present
      // setIsLoadingHistory(true);
      // getSessionHistory(currentUser.uid, sessionIdFromParams) // Assuming getSessionHistory takes userId and sessionId
      //   .then(history => {
      //     // const formattedMessages = history.interactions.map(interactionToDisplayMessage); // Define this mapper
      //     // setInitialMessages(formattedMessages);
      //     console.log("Formatted messages would be set here.");
      //   })
      //   .catch(err => setPageError(`Failed to load session history: ${err.message}`))
      //   .finally(() => setIsLoadingHistory(false));
      console.log("Existing session ID provided:", sessionIdFromParams, "- history loading not yet implemented.");
    }
  }, [currentUser, sessionIdFromParams, isInitialized, authLoading]);


  // Placeholder function to simulate fetching/generating summary
  const handleFetchPatientSummary = async () => {
    if (!currentUser) return;
    setSummaryLoading(true);
    setSummaryError(null);
    await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate API call

    const rand = Math.random();
    if (rand < 0.6) {
        setSummaryContent(`This is a sample patient summary for user ${currentUser.displayName || currentUser.uid}.

Key observations:
- Blood pressure slightly elevated on last check.
- Reported mild headache yesterday.

Recommendations:
- Continue monitoring blood pressure.
- Ensure adequate hydration.
 (Summary generated: ${new Date().toLocaleTimeString()})`);
    } else if (rand < 0.8) {
        setSummaryError("Failed to generate summary due to a temporary issue with the AI model.");
        setSummaryContent(null);
    } else {
        setSummaryContent(null); // "No significant data available..." handled by component
    }
    setSummaryLoading(false);
  };

  useEffect(() => {
    if(currentUser) {
        handleFetchPatientSummary(); // Fetch summary on initial load or when user context is available
    }
  }, [currentUser]); // Dependency on currentUser ensures it runs once user is loaded

  if (authLoading || !isInitialized || (!currentSessionId && !pageError && !isLoadingHistory)) {
    // Extended loading condition to also consider if history is being loaded for an existing session
    return <Center style={{ height: '80vh' }}><Loader size="lg" /></Center>;
  }

  if (!currentUser) { // Should be caught by ProtectedRoute, but as a safeguard
    return <Navigate to="/login" replace />;
  }

  if (pageError) {
    return (
      <Container size="md" py="xl">
        <Alert title="Chat Page Error" color="noahRed" icon={<IconAlertCircle />}>
          {pageError}
        </Alert>
      </Container>
    );
  }

  // Calculate available height for ChatInterface more reliably
  // This is a rough estimate, depends on other elements in AppShell.Main and on the page
  // Adjusted based on typical AppShell structure. The accordion panels also add some padding/margin.
  const chatInterfaceHeight = `calc(100vh - var(--app-shell-header-height, 60px) - 2 * var(--mantine-spacing-md) - 150px)`; // ~150px for accordion controls, page group button, etc.


  return (
    // Changed Container to Box for direct flex control and to make it the main flex container for the page content
    <Box style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 'var(--mantine-spacing-xs)' }}>
      {/* Optional: Button to trigger PatientDataLogModal from ChatPage directly */}
      <Group justify="flex-end" pb="xs"> {/* Added padding bottom for spacing */}
          <Button
            onClick={openLogDataModal}
            variant="light"
            leftSection={<IconNotes size="1rem"/>}
          >
            Log Patient Data
          </Button>
      </Group>

      <Accordion chevronPosition="left" variant="separated" defaultValue={["chat_interface"]} multiple style={{flexGrow: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column'}}>
        <Accordion.Item value="patient_summary" style={{overflow: 'auto'}}> {/* Allow summary panel to scroll if content is large */}
          <Accordion.Control icon={<IconNotes size="1.2rem" />}>
            Patient AI Summary
          </Accordion.Control>
          <Accordion.Panel>
            <PatientSummaryDisplay
              summaryContent={summaryContent}
              isLoading={summaryLoading}
              error={summaryError}
            />
             <Tooltip label="Refresh Summary" position="bottom" withArrow>
                 <ActionIcon variant="subtle" onClick={handleFetchPatientSummary} mt="sm" disabled={summaryLoading}>
                    <IconRefresh size="1.1rem" />
                 </ActionIcon>
             </Tooltip>
          </Accordion.Panel>
        </Accordion.Item>

        <Accordion.Item value="chat_interface" style={{flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden'}}> {/* Chat item takes remaining space */}
          <Accordion.Control icon={<IconMessageChatbot size="1.2rem" />}>
            Chat with Noah.AI RN
          </Accordion.Control>
          <Accordion.Panel style={{flexGrow: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column'}}>
             {/* Ensure ChatInterface is only rendered when session ID is available */}
            {currentSessionId && currentUser ? (
                <Box style={{flexGrow:1, height: chatInterfaceHeight, minHeight: 300, display: 'flex', flexDirection: 'column'}}> {/* Ensure Box takes available space */}
                    <ChatInterface
                        key={currentSessionId} // Re-mounts if session ID changes
                        initialMessages={initialMessages}
                        currentUserId={currentUser.uid}
                        initialSessionId={currentSessionId}
                        // onNewSessionNeeded={handleNewSession} // Optional: if ChatInterface needs to signal page for new session
                    />
                </Box>
            ) : (
                !pageError && <Center style={{flexGrow:1}}><Loader/></Center> // Show loader if session ID not yet set and no page error
            )}
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>

      {/* Modal for Patient Data Logging (triggered by button on this page) */}
      {currentUser && (
        <PatientDataLogModal
            opened={logDataModalOpened}
            onClose={closeLogDataModal}
            patientId={currentUser.uid} // Or a selected patient ID. For now, user's own ID.
        />
      )}
    </Box>
  );
};

export default ChatPage;
