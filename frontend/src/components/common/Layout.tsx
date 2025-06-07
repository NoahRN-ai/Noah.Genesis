```tsx
import React, { useState } from 'react';
import { AppShell, Burger, Group, NavLink, Text, useMantineTheme, useMantineColorScheme, ActionIcon, Modal, Title, ThemeIcon, Box, Button, UnstyledButton, Tooltip } from '@mantine/core'; // Added Modal, Title, ThemeIcon, Box, Button, UnstyledButton, Tooltip
import { IconSun, IconMoonStars, IconUserCircle, IconSettings, IconLogout, IconMessageChatbot, IconFileDescription } from '@tabler/icons-react'; // Added IconFileDescription, removed unused
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { notifications } from '@mantine/notifications';
import { PatientDataForm } from '../PatientDataForm';
import { useDisclosure } from '@mantine/hooks';

// Noah Logo Component (Placeholder - replace with actual SVG or Image) - Kept from existing
const NoahLogo = () => (
  <Group gap="xs">
    <svg width="32" height="32" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="45" fill="#FFC107"/> {/* Example color, can be themed */}
        <text x="50" y="62" fontFamily="Arial, sans-serif" fontSize="40" fontWeight="bold" textAnchor="middle" fill="#3A3A3A">N</text>
    </svg>
    <Text size="xl" fw={700} c="noahDarkGray.7">
      Noah.AI RN
    </Text>
  </Group>
);

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const theme = useMantineTheme();
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
  const [opened, setOpened] = useState(false); // For mobile nav
  const { currentUser, signOutUser, firebaseUser } = useAuth(); // signOutUser from new code
  const navigate = useNavigate();
  const location = useLocation();

  const [logDataModalOpened, { open: openLogDataModal, close: closeLogDataModal }] = useDisclosure(false);

  const handleSignOut = async () => {
    try {
      await signOutUser(); // Using signOutUser from new code
      notifications.show({ title: 'Signed Out', message: 'You have been successfully signed out.', color: 'noahGreen' });
      navigate('/login');
    } catch (error: any) {
      notifications.show({ title: 'Sign Out Error', message: error.message, color: 'noahRed' });
    }
  };

  // NavLinks definition from new code, ensuring firebaseUser is checked for profile link
  const navLinks = currentUser && firebaseUser ? [
    { icon: IconMessageChatbot, label: 'Chat', path: '/chat', action: () => navigate('/chat') },
    { icon: IconUserCircle, label: 'Profile', path: `/profile/${firebaseUser.uid}`, action: () => navigate(`/profile/${firebaseUser.uid}`) },
    // { icon: IconSettings, label: 'Settings', path: '/settings', action: () => navigate('/settings') }, // Settings page is placeholder
  ] : [];

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 250, breakpoint: 'sm', collapsed: { mobile: !opened, desktop: !currentUser } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            {currentUser && ( // Burger only if user is logged in and navbar is present
              <Burger opened={opened} onClick={() => setOpened((o) => !o)} size="sm" hiddenFrom="sm" />
            )}
            {/* UnstyledButton kept from existing, Title color from new */}
            <UnstyledButton component={Link} to={currentUser ? "/chat" : "/login"}>
                <Title order={3} c="noahBlue.8">Noah.AI RN</Title>
            </UnstyledButton>
          </Group>
          <Group>
            {/* Tooltip kept from existing, ActionIcon structure is similar */}
            <Tooltip label={colorScheme === 'dark' ? 'Light mode' : 'Dark mode'} position="bottom">
              <ActionIcon variant="default" onClick={() => toggleColorScheme()} size="lg">
                {colorScheme === 'dark' ? <IconSun stroke={1.5} /> : <IconMoonStars stroke={1.5} />}
              </ActionIcon>
            </Tooltip>
            {!currentUser && location.pathname !== '/login' && (
              <Button component={Link} to="/login" variant="default">Sign In</Button>
            )}
          </Group>
        </Group>
      </AppShell.Header>

      {currentUser && firebaseUser && ( // Navbar only if user and firebaseUser details are present
        <AppShell.Navbar p="md">
          <AppShell.Section grow>
            {navLinks.map((item) => (
              <NavLink
                key={item.label}
                active={location.pathname === item.path}
                label={item.label}
                leftSection={<item.icon size="1rem" stroke={1.5} />}
                onClick={() => { item.action(); setOpened(false); }} // item.action for navigation
                variant="subtle"
                color={theme.primaryColor} // Kept from existing
              />
            ))}
            {/* Button to open Log Data Modal directly from Navbar */}
            <NavLink
                mt="sm"
                label="Log Patient Data"
                leftSection={<IconFileDescription size="1rem" stroke={1.5}/>}
                onClick={() => { openLogDataModal(); setOpened(false); }}
                variant="filled"
                color="noahGreen"
            />
          </AppShell.Section>
          <AppShell.Section>
            <NavLink
              label="Sign Out"
              leftSection={<IconLogout size="1rem" stroke={1.5} />}
              onClick={handleSignOut}
              color="noahRed" // color from new, variant from existing
              variant="subtle"
            />
            {/* User info box from new code */}
             <Box mt="sm" p="xs" style={{ borderTop: `1px solid ${theme.colors.gray[3]}`}}>
                <Text size="xs" c="dimmed">User: {currentUser.email}</Text>
                <Text size="xs" c="dimmed">UID: {firebaseUser.uid}</Text>
            </Box>
          </AppShell.Section>
        </AppShell.Navbar>
      )}

      <AppShell.Main>
        {children}
      </AppShell.Main>

      {/* Modal for Patient Data Logging */}
      {currentUser && firebaseUser && ( // Ensure firebaseUser for targetPatientUserId
        <Modal
          opened={logDataModalOpened}
          onClose={closeLogDataModal}
          title={
            <Group>
                <ThemeIcon variant="light" color="noahGreen" size="lg"><IconFileDescription/></ThemeIcon>
                <Title order={3} ff="Greycliff CF, sans-serif">Log New Patient Data</Title>
            </Group>
          }
          size="lg"
          radius="md"
          overlayProps={{
            backgroundOpacity: 0.55,
            blur: 3,
          }}
          centered
        >
          <PatientDataForm
            targetPatientUserId={firebaseUser.uid}
            onSubmitSuccess={() => {
              closeLogDataModal();
              notifications.show({title: 'Data Logged via Modal', message: 'Patient data successfully submitted.', color: 'noahGreen'});
            }}
            onCancel={closeLogDataModal}
          />
        </Modal>
      )}
    </AppShell>
  );
};

// Export NoahLogo if it's intended to be used elsewhere - Kept from existing
export { NoahLogo };
```
