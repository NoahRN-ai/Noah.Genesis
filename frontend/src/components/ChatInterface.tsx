```tsx
import React, { useState, useEffect, useRef, FormEvent, KeyboardEvent } from 'react';
import {
  Box, Paper, ScrollArea, Stack, Group, Avatar, Text, Textarea, ActionIcon,
  Loader, useMantineTheme, Tooltip, Kbd, UnstyledButton, ThemeIcon, rem,
  SegmentedControl, // Import SegmentedControl
  Center, // For initial empty message
} from '@mantine/core';
import {
  IconSend, IconUser, IconRobotFilled, IconMicrophone, IconAlertTriangleFilled,
  IconInfoCircleFilled, IconPlayerStopFilled, IconReload
} from '@tabler/icons-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { v4 as uuidv4 } from 'uuid';
import { format, parseISO, isValid } from 'date-fns';
import { notifications } from '@mantine/notifications';

import { DisplayMessage, ToolCallData } from '../types/api';
import { sendChatMessage } from '../services/chatApiService';
// For a more distinct Noah AI avatar:
// const NoahAgentAvatar: React.FC = () => (
//   <ThemeIcon size="lg" radius="xl" variant="gradient" gradient={{ from: 'blue', to: 'cyan' }}>
//     <IconRobotFilled style={{ width: '70%', height: '70%' }} />
//   </ThemeIcon>
// );

const NoahAgentAvatar: React.FC = () => {
  const theme = useMantineTheme();
  return (
    <ThemeIcon size={rem(36)} radius="xl" variant="gradient" gradient={{ from: theme.colors.noahBlue[6], to: theme.colors.noahBlue[4], deg: 105 }}>
      <IconRobotFilled style={{ width: rem(20), height: rem(20) }} stroke={1.5} />
    </ThemeIcon>
  );
};


const UserAvatar: React.FC = () => {
  const theme = useMantineTheme();
  return (
    <ThemeIcon size={rem(36)} radius="xl" variant="outline" color={theme.colors.noahDarkGray[3]}>
        <IconUser style={{ width: rem(20), height: rem(20) }} stroke={1.5} />
    </ThemeIcon>
  );
}

const useStyles = (theme: ReturnType<typeof useMantineTheme>) => ({ // Pass theme explicitly
  messageRow: {
    display: 'flex',
    flexDirection: 'row' as 'row',
    marginBottom: theme.spacing.md,
    gap: theme.spacing.sm,
  },
  userMessageRow: {
    flexDirection: 'row-reverse' as 'row-reverse',
  },
  messageBubbleBase: {
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    borderRadius: theme.radius.lg,
    maxWidth: '80%',
    wordWrap: 'break-word' as 'break-word',
    boxShadow: theme.shadows.sm,
    border: `1px solid ${theme.colors.noahDarkGray[2]}`,
    position: 'relative' as 'relative', // For potential timestamp absolutely positioned inside
  },
  userMessageBubble: {
    backgroundColor: theme.colors.noahBlue[6],
    color: theme.white,
    borderBottomRightRadius: theme.radius.xs,
    borderColor: theme.colors.noahBlue[7],
  },
  agentMessageBubble: {
    backgroundColor: theme.colorScheme === 'dark' ? theme.colors.noahDarkGray[8] : theme.white,
    color: theme.colorScheme === 'dark' ? theme.colors.noahDarkGray[0] : theme.black,
    borderBottomLeftRadius: theme.radius.xs,
  },
  systemMessageBubble: { // For system status or errors shown in chat flow
    backgroundColor: theme.colors.noahDarkGray[1],
    color: theme.colors.noahDarkGray[7],
    alignSelf: 'center',
    textAlign: 'center' as 'center',
    fontSize: theme.fontSizes.sm,
    padding: `${theme.spacing.xs} ${theme.spacing.md}`,
    border: `1px solid ${theme.colors.noahDarkGray[3]}`,
    width: 'fit-content',
    margin: `${theme.spacing.sm} auto`,
  },
  errorDisplayBubble: { // For agent-returned errors displayed as a message
    backgroundColor: theme.colors.noahRed[0],
    color: theme.colors.noahRed[8], // Dark red text for better contrast
    border: `1px solid ${theme.colors.noahRed[3]}`,
  },
  markdownContent: {
    '& p': { margin: 0, marginBottom: theme.spacing.xs, lineHeight: 1.6 },
    '& ul, & ol': { paddingLeft: theme.spacing.lg, margin: `${theme.spacing.xs} 0`, lineHeight: 1.6 },
    '& li': { marginBottom: theme.spacing.xs / 2 },
    '& strong': { fontWeight: 600 },
    '& a': {
      color: theme.colors.noahBlue[theme.fn.primaryShade()],
      textDecoration: 'none',
      '&:hover': { textDecoration: 'underline' }
    },
    '& pre': {
      backgroundColor: theme.colorScheme === 'dark' ? theme.colors.noahDarkGray[8] : theme.colors.noahDarkGray[0],
      border: `1px solid ${theme.colors.noahDarkGray[2]}`,
      padding: theme.spacing.sm,
      borderRadius: theme.radius.sm,
      overflowX: 'auto' as 'auto',
      fontSize: '0.9em',
      lineHeight: 1.45,
    },
    '& code:not(pre code)': { // Inline code
      backgroundColor: theme.colorScheme === 'dark' ? theme.colors.noahDarkGray[6] : theme.colors.noahDarkGray[1],
      padding: `${rem(2)} ${rem(5)}`,
      borderRadius: theme.radius.sm,
      fontSize: '0.9em',
      border: `1px solid ${theme.colors.noahDarkGray[2]}`,
    },
  },
  avatarBox: { // Ensures avatar aligns with the start of the message bubble text
    display: 'flex',
    alignItems: 'flex-end', // Pushes avatar to bottom
    paddingBottom: rem(3), // Fine-tune vertical alignment with bubble
  },
  timestampText: {
    fontSize: theme.fontSizes.xs,
    color: theme.colors.noahDarkGray[5],
    marginTop: rem(2),
    textAlign: 'right' as 'right',
  },
  messageWrapper: { // New wrapper for bubble + timestamp below it
    display: 'flex',
    flexDirection: 'column' as 'column',
    maxWidth: '80%', // To match bubble's maxWidth
    alignItems: 'stretch' as 'stretch', // Ensure bubble takes up maxWidth potential
  },
   userMessageWrapper: {
    alignItems: 'flex-end' as 'flex-end',
  },
  agentMessageWrapper: {
    alignItems: 'flex-start' as 'flex-start',
  },
});

interface ChatMessageDisplayProps {
  message: DisplayMessage;
}

const ChatMessageDisplay: React.FC<ChatMessageDisplayProps> = React.memo(({ message }) => {
  const theme = useMantineTheme();
  const classes = useStyles(theme); // Pass theme to useStyles

  const isUser = message.sender === 'user';
  const isAgent = message.sender === 'agent';
  const isSystem = message.sender === 'system';

  let bubbleSpecificStyle = {};
  if (isUser) bubbleSpecificStyle = classes.userMessageBubble;
  else if (isAgent) bubbleSpecificStyle = classes.agentMessageBubble;

  if (message.isError && (isAgent || isSystem)) {
    bubbleSpecificStyle = {...bubbleSpecificStyle, ...classes.errorDisplayBubble };
  }

  const formattedTimestamp = () => {
    if (!message.timestamp) return '';
    const date = typeof message.timestamp === 'string' ? parseISO(message.timestamp) : message.timestamp;
    return isValid(date) ? format(date, 'HH:mm') : ''; // e.g., 10:35
  };

  if (isSystem && !message.isTyping) { // System messages like errors (not typing indicator)
    return (
      <Paper style={{...classes.messageBubbleBase, ...classes.systemMessageBubble, ...(message.isError && classes.errorDisplayBubble) }} withBorder shadow="xs">
         {message.isError && <IconAlertTriangleFilled size="1.1rem" style={{ marginRight: theme.spacing.xs, verticalAlign: 'middle' }} />}
        <Text component="span">{message.text}</Text>
      </Paper>
    );
  }

  return (
    <Box className={`${classes.messageRow} ${isUser ? classes.userMessageRow : ''}`}>
      <Box className={classes.avatarBox}>
        {isUser ? <UserAvatar /> : (isAgent || (isSystem && message.isTyping) ? <NoahAgentAvatar /> : null)}
      </Box>
      <Box className={`${classes.messageWrapper} ${isUser ? classes.userMessageWrapper : classes.agentMessageWrapper}`}>
        <Paper style={{...classes.messageBubbleBase, ...bubbleSpecificStyle}} shadow="sm" withBorder={!isUser}>
            <Box style={classes.markdownContent}>
                {message.isTyping ? (
                <Group gap="xs" align="center">
                    <Loader size="xs" type="dots" color={theme.colors.noahDarkGray[5]} />
                    {/* Removed redundant "Noah.AI is typing..." text as loader implies it from agent */}
                </Group>
                ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.text}</ReactMarkdown>
                )}
            </Box>
            {/* Placeholder for Tool Calls (Minimal display for MVP as requested) */}
            {isAgent && message.tool_calls && message.tool_calls.length > 0 && !message.isTyping && (
                <Text size="xs" c={isUser ? theme.colors.noahBlue[0] : theme.colors.noahDarkGray[5]} mt="xs" fs="italic">
                    (Considering tools: {message.tool_calls.map(tc => tc.name).join(', ')})
                </Text>
            )}
        </Paper>
        {message.timestamp && !message.isTyping && (
            <Text className={classes.timestampText} style={{ textAlign: isUser ? 'right' : 'left', paddingRight: isUser ? rem(5) : 0, paddingLeft: !isUser ? rem(5) : 0 }}>
                {formattedTimestamp()}
            </Text>
        )}
      </Box>
    </Box>
  );
});

interface ChatInterfaceProps {
  initialMessages?: DisplayMessage[];
  currentUserId: string;
  initialSessionId: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  initialMessages = [],
  currentUserId, // used for logging or future features tied to user
  initialSessionId,
}) => {
  const theme = useMantineTheme();
  const [messages, setMessages] = useState<DisplayMessage[]>(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false); // Renamed from isLoading for clarity
  const [currentSessionId, setCurrentSessionId] = useState<string>(initialSessionId);
  const [chatMode, setChatMode] = useState<string>("default"); // State for chat mode

  const scrollViewport = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => { // Auto-scroll
    scrollViewport.current?.scrollTo({ top: scrollViewport.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  useEffect(() => { // Focus input on load or after message send
    textareaRef.current?.focus();
  }, [isSending]); // Re-focus when not sending (i.e., after send completes)


  const addDisplayMessage = (messageData: Omit<DisplayMessage, 'id' | 'timestamp'> & { id?: string, timestamp?: Date | string }) => {
    const newMessage: DisplayMessage = {
      id: messageData.id || uuidv4(),
      text: messageData.text,
      sender: messageData.sender,
      timestamp: messageData.timestamp || new Date(),
      isTyping: messageData.isTyping,
      isError: messageData.isError,
      tool_calls: messageData.tool_calls,
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const showAgentTypingIndicator = (show: boolean) => {
    setMessages((prev) => {
      const existingTyping = prev.find(m => m.isTyping);
      if (show && !existingTyping) {
        return [...prev, { id: 'agent-typing-indicator', text: '', sender: 'agent', isTyping: true, timestamp: new Date() }];
      }
      if (!show && existingTyping) {
        return prev.filter(m => !m.isTyping);
      }
      return prev;
    });
  };

  const handleSendMessage = async (e?: FormEvent<HTMLFormElement> | KeyboardEvent<HTMLTextAreaElement>) => {
    if (e && 'preventDefault' in e) e.preventDefault();
    const queryText = inputValue.trim();
    if (!queryText || isSending) return;

    addDisplayMessage({ text: queryText, sender: 'user' });
    setInputValue('');
    setIsSending(true);
    showAgentTypingIndicator(true);

    try {
      // Pass the chatMode in the payload
      const response = await sendChatMessage({
        user_query_text: queryText,
        session_id: currentSessionId,
        mode: chatMode, // Include the selected chat mode
      });

      addDisplayMessage({
        id: response.interaction_id,
        text: response.agent_response_text,
        sender: 'agent',
        // Assuming backend's timestamp for agent message will be handled if available
        // tool_calls: response.tool_calls_data_if_any // If backend structures this for frontend
      });
      setCurrentSessionId(response.session_id);
    } catch (error: any) {
      console.error('ChatInterface: API Error:', error);
      addDisplayMessage({
        text: error.message || 'An unexpected error occurred connecting to Noah.AI.',
        sender: 'system',
        isError: true,
      });
      notifications.show({
        title: 'Chat Connection Error',
        message: error.message || 'Could not communicate with Noah.AI. Please ensure you are connected and try again.',
        color: 'noahRed',
        icon: <IconAlertTriangleFilled size="1.2rem" />,
        autoClose: 7000,
      });
    } finally {
      showAgentTypingIndicator(false);
      setIsSending(false);
    }
  };

  const handleTextareaKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !isSending) {
      event.preventDefault();
      handleSendMessage(event);
    }
  };

  return (
    <Box style={{ display: 'flex', flexDirection: 'column', height: '100%', flexGrow: 1, backgroundColor: theme.colorScheme === 'dark' ? theme.colors.noahDarkGray[9] : theme.colors.noahDarkGray[0] }}>
      {/* Mode Selector - Placed above the message list or input area */}
      <Paper p="xs" withBorder radius={0} style={{
          backgroundColor: theme.colorScheme === 'dark' ? theme.colors.noahDarkGray[8] : theme.white,
          borderBottom: `${rem(1)} solid ${theme.colorScheme === 'dark' ? theme.colors.noahDarkGray[7] : theme.colors.noahDarkGray[2]}`,
          // Approximately 45-50px height with padding
        }}>
        <Group justify="center"> {/* Center the segmented control */}
          <SegmentedControl
            value={chatMode}
            onChange={setChatMode} // Directly use setChatMode if no other logic needed
            data={[
              { label: 'Noah AI RN (Default)', value: 'default' },
              { label: 'Hippocrates (Research)', value: 'hippocrates' },
            ]}
            color="noahBlue" // Use a color from your theme
            size="sm" // Adjust size as needed
          />
        </Group>
      </Paper>

      <ScrollArea.Autosize mah={'calc(100% - 90px - 50px)'} /* Adjusted for mode selector height (input area 90px + mode selector ~50px) */ viewportRef={scrollViewport} style={{ flexGrow: 1 }} p="md" type="auto">
        <Stack gap="md" pb="xl">
          {messages.length === 0 && !isSending && (
            // Center component from Mantine can be used for better vertical centering
            <Center style={{ height: 'calc(100vh - 90px - 50px - 100px)', opacity: 0.6 }}>
              {/* Adjust height considering other elements and desired empty state appearance */}
            {/* Center component from Mantine can be used for better vertical centering */}
            <Center style={{ height: 'calc(100vh - 90px - 50px - 100px)', opacity: 0.6 }}>
              {/* Adjust height considering other elements and desired empty state appearance */}
              <Stack align="center" gap="xs">
                <NoahAgentAvatar/>
                <Text size="lg" c="dimmed">Noah.AI RN is ready.</Text>
                <Text size="sm" c="dimmed">How can I help you today?</Text>
              </Stack>
            </Center>
          )}
          {messages.map((msg) => (
            <ChatMessageDisplay key={msg.id} message={msg} />
          ))}
        </Stack>
      </ScrollArea>

      <Paper
        component="form"
        onSubmit={handleSendMessage} // This will be updated in the next step to include chatMode
        p="md"
        radius={0}
        style={{
          backgroundColor: theme.colorScheme === 'dark' ? theme.colors.noahDarkGray[8] : theme.white,
          borderTop: `${rem(1)} solid ${theme.colorScheme === 'dark' ? theme.colors.noahDarkGray[7] : theme.colors.noahDarkGray[2]}`,
        }}
      >
        <Group align="flex-end" wrap="nowrap" gap="sm">
          <Textarea
            ref={textareaRef}
            placeholder="Type your message to Noah.AI RN..."
            value={inputValue}
            onChange={(event) => setInputValue(event.currentTarget.value)}
            onKeyDown={handleTextareaKeyDown}
            disabled={isSending}
            minRows={1}
            maxRows={5}
            autosize
            style={{ flexGrow: 1 }}
            radius="xl" // Rounded textarea
            rightSectionWidth={rem(42)}
            rightSection={
              <Tooltip label="Voice input (coming soon)" position="top-end" withArrow withinPortal>
                <ActionIcon size={32} radius="xl" variant="subtle" disabled style={{marginRight: rem(2)}}>
                  <IconMicrophone size="1.1rem" stroke={1.5} />
                </ActionIcon>
              </Tooltip>
            }
            variant="filled"
          />
          <ActionIcon
            type="submit"
            size={38}
            radius="xl"
            color="noahBlue"
            variant={isSending || !inputValue.trim() ? "filled" : "gradient"}
            gradient={!isSending && inputValue.trim() ? { from: theme.colors.noahBlue[5], to: theme.colors.noahBlue[7], deg: 135 } : undefined}
            disabled={isSending || !inputValue.trim()}
            aria-label="Send message"
          >
            {isSending ? <Loader size={rem(20)} color="white" type="oval" /> : <IconSend size="1.2rem" stroke={1.5} />}
          </ActionIcon>
        </Group>
        <Text size="xs" c="dimmed" mt={rem(5)} ta="right">
          <Kbd>Shift</Kbd> + <Kbd>Enter</Kbd> for newline
        </Text>
      </Paper>
    </Box>
  );
};
```
