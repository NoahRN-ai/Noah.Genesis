```tsx
import React, { ReactNode, useState } from 'react';
import { AppShell, Burger, Group, Header, MediaQuery, Navbar, Text, useMantineTheme, Button, NavLink, Box, Kbd, UnstyledButton, Tooltip, ActionIcon, useMantineColorScheme } from '@mantine/core';
import {
  IconHome, IconUserCircle, IconLogout, IconMessageChatbot, IconFileText, IconSettings,
  IconSun, IconMoonStars, IconMicrophone // Placeholder for voice input
} from '@tabler/icons-react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

// Noah Logo Component (Placeholder - replace with actual SVG or Image)
const NoahLogo = () => (
  <Group gap="xs">
     {/* Placeholder for actual logo image/SVG */}
    <svg width="32" height="32" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="45" fill="#FFC107"/>
        <text x="50" y="62" fontFamily="Arial, sans-serif" fontSize="40" fontWeight="bold" textAnchor="middle" fill="#3A3A3A">N</text>
    </svg>
    <Text size="xl" fw={700} c="noahDarkGray.7"> {/* Using theme color */}
      Noah.AI RN
    </Text>
  </Group>
);


interface AppLayoutProps {
  children: ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const theme = useMantineTheme();
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
  const [opened, setOpened] = useState(false);
  const { currentUser, signOut, firebaseUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleSignOut = async () => {
    try {
      await signOut();
      navigate('/login', { replace: true });
    } catch (error) {
      console.error("Error during sign out:", error);
      // Consider using Mantine notifications for user feedback
    }
  };

  const navLinks = currentUser ? [
    { icon: IconMessageChatbot, label: 'Chat', path: '/chat' },
    // { icon: IconFileText, label: 'Log Data', path: '/patient-data' }, // Form might be a modal within ChatPage
    { icon: IconUserCircle, label: 'Profile', path: `/profile/${firebaseUser?.uid || 'me'}` }, // Ensure firebaseUser.uid is used
    { icon: IconSettings, label: 'Settings', path: '/settings' },
  ] : [];

  return (
    <AppShell
      padding="md"
      navbarOffsetBreakpoint="sm"
      header={{ height: 60 }}
      navbar={ currentUser ? {
        width: { sm: 200, lg: 250 },
        breakpoint: 'sm',
        collapsed: { mobile: !opened },
      } : undefined }
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            {currentUser && (
              <Burger opened={opened} onClick={() => setOpened((o) => !o)} hiddenFrom="sm" size="sm" />
            )}
            <UnstyledButton component={Link} to={currentUser ? "/chat" : "/login"}>
                <NoahLogo />
            </UnstyledButton>
          </Group>

          <Group>
            <Tooltip label={colorScheme === 'dark' ? 'Light mode' : 'Dark mode'} position="bottom">
              <ActionIcon
                variant="outline"
                color={colorScheme === 'dark' ? 'yellow' : 'blue'}
                onClick={() => toggleColorScheme()}
                title="Toggle color scheme"
              >
                {colorScheme === 'dark' ? <IconSun size="1.2rem" /> : <IconMoonStars size="1.2rem" />}
              </ActionIcon>
            </Tooltip>
            {!currentUser && (
              <Button component={Link} to="/login" variant="light">
                Sign In
              </Button>
            )}
          </Group>
        </Group>
      </AppShell.Header>

      {currentUser && (
        <AppShell.Navbar p="md">
          <AppShell.Section grow>
            {navLinks.map((item) => (
              <NavLink
                key={item.label}
                active={location.pathname === item.path}
                label={item.label}
                leftSection={<item.icon size="1rem" stroke={1.5} />}
                component={Link}
                to={item.path}
                onClick={() => setOpened(false)} // Close on mobile nav click
                variant="subtle"
                color={theme.primaryColor}
              />
            ))}
          </AppShell.Section>
          <AppShell.Section> {/* Footer of Navbar */}
            <NavLink
              label="Sign Out"
              leftSection={<IconLogout size="1rem" stroke={1.5} />}
              onClick={handleSignOut}
              color="red"
              variant="subtle"
            />
          </AppShell.Section>
        </AppShell.Navbar>
      )}

      <AppShell.Main>
        {/* Ensure children fill the main area if needed */}
        {children}
      </AppShell.Main>
    </AppShell>
  );
};

// Export NoahLogo if it's intended to be used elsewhere, e.g. LoginPage
// Otherwise, it can remain a local component within Layout.tsx
export { NoahLogo };
```
