```tsx
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  TextInput, PasswordInput, Button, Paper, Title, Text, Container,
  Group, Alert, Divider, LoadingOverlay, Anchor, Stack, Center
} from '@mantine/core';
import { useForm, zodResolver } from '@mantine/form'; // zodResolver for advanced validation
import { z } from 'zod'; // Zod for schema validation
import { IconAlertCircle, IconLogin, IconUserPlus } from '@tabler/icons-react';
// Assuming IconBrandGoogle is imported correctly from @tabler/icons-react or similar
import { IconBrandGoogle } from '@tabler/icons-react';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  googleProvider,
  authInstance,
  firebaseUpdateProfile,
  User as FirebaseUser
} from '../services/firebaseService';
import { useAuth } from '../hooks/useAuth';
import { notifications } from '@mantine/notifications';
import { NoahLogo } from '../components/common/Layout'; // Assuming NoahLogo is exported from Layout or moved to common

// Zod validation schemas
const loginSchema = z.object({
  email: z.string().email({ message: 'Invalid email address' }),
  password: z.string().min(6, { message: 'Password must be at least 6 characters long' }),
});

const registerSchema = z.object({
  displayName: z.string().min(2, { message: 'Display name must be at least 2 characters' }).optional(),
  email: z.string().email({ message: 'Invalid email address' }),
  password: z.string().min(6, { message: 'Password must be at least 6 characters long' }),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'], // path of error
});


const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentUser, isLoading: authIsLoading, isInitialized } = useAuth();

  const [isLoginMode, setIsLoginMode] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formLoading, setFormLoading] = useState(false);

  // Redirect if user is already logged in and auth is initialized
  useEffect(() => {
    if (isInitialized && currentUser) {
      const from = (location.state as any)?.from?.pathname || '/chat';
      notifications.show({
        title: `Welcome back, ${currentUser.displayName || currentUser.email}!`,
        message: 'Redirecting you to the chat...',
        color: 'green',
      });
      navigate(from, { replace: true });
    }
  }, [currentUser, isInitialized, navigate, location.state]);

  const form = useForm({
    validate: zodResolver(isLoginMode ? loginSchema : registerSchema),
    initialValues: {
      email: '',
      password: '',
      confirmPassword: '',
      displayName: '', // For registration
    },
  });

  const handleSubmit = async (values: typeof form.values) => {
    setFormLoading(true);
    setError(null);
    try {
      let userCredential;
      if (isLoginMode) {
        userCredential = await signInWithEmailAndPassword(authInstance, values.email, values.password);
        notifications.show({ title: 'Login Successful', message: 'Welcome back!', color: 'green' });
      } else {
        userCredential = await createUserWithEmailAndPassword(authInstance, values.email, values.password);
        if (userCredential.user && values.displayName) {
          await firebaseUpdateProfile(userCredential.user, { displayName: values.displayName });
        }
        notifications.show({ title: 'Registration Successful', message: 'Welcome to Noah.AI! Please log in.', color: 'green' });
        setIsLoginMode(true); // Switch to login mode after successful registration
        form.reset(); // Reset form for login
      }
      // Firebase onAuthStateChanged in AuthContext will handle navigation.
    } catch (err: any) {
      const firebaseError = err.code ? (err.code.replace('auth/', '').split('-').join(' ') ) : 'Authentication failed.';
      setError(firebaseError.charAt(0).toUpperCase() + firebaseError.slice(1) || `Failed to ${isLoginMode ? 'login' : 'register'}. Please try again.`);
      console.error(err);
      notifications.show({ title: 'Authentication Error', message: error || 'An error occurred.', color: 'red' });
    } finally {
      setFormLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setFormLoading(true);
    setError(null);
    try {
      await signInWithPopup(authInstance, googleProvider);
      notifications.show({ title: 'Google Sign-In Successful', message: 'Welcome!', color: 'green' });
      // onAuthStateChanged will handle navigation
    } catch (err: any) {
      const firebaseError = err.code ? (err.code.replace('auth/', '').split('-').join(' ') ) : 'Google Sign-In failed.';
      setError(firebaseError.charAt(0).toUpperCase() + firebaseError.slice(1) || 'Failed to sign in with Google. Please try again.');
      console.error(err);
       notifications.show({ title: 'Google Sign-In Error', message: error || 'An error occurred.', color: 'red' });
    } finally {
      setFormLoading(false);
    }
  };

  // Show loading overlay for the whole page if auth state is loading from AuthContext
  if (authIsLoading && !isInitialized) {
     return (
      <Center style={{ height: '100vh' }}>
        <Loader size="xl" />
      </Center>
    );
  }

  // If user becomes authenticated while on this page (e.g. through another tab), effect will redirect.
  // This check avoids rendering form if already logged in but effect hasn't run yet.
  if (currentUser) return null;

  return (
    <Container size={460} my={40} style={{ minHeight: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
      <Center mb="xl">
        <NoahLogo />
      </Center>
      <Title ta="center" ff={'Greycliff CF, sans-serif'} fw={700} order={2}>
        {isLoginMode ? 'Welcome back to Noah.AI RN' : 'Join Noah.AI RN'}
      </Title>
      <Text c="dimmed" size="sm" ta="center" mt={5} mb={30}>
        {isLoginMode ? (
          <>
            Don&apos;t have an account?{' '}
            <Anchor component="button" type="button" size="sm" onClick={() => { setIsLoginMode(false); setError(null); form.reset(); }}>
              Sign Up
            </Anchor>
          </>
        ) : (
          <>
            Already have an account?{' '}
            <Anchor component="button" type="button" size="sm" onClick={() => { setIsLoginMode(true); setError(null); form.reset(); }}>
              Sign In
            </Anchor>
          </>
        )}
      </Text>

      <Paper withBorder shadow="md" p={30} radius="md" pos="relative">
        <LoadingOverlay visible={formLoading} overlayProps={{ radius: 'sm', blur: 2 }} />
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack gap="md">
            {!isLoginMode && (
              <TextInput
                label="Display Name"
                placeholder="Your Name"
                {...form.getInputProps('displayName')}
              />
            )}
            <TextInput
              required
              label="Email"
              placeholder="hello@noah.ai"
              {...form.getInputProps('email')}
              error={form.errors.email}
            />
            <PasswordInput
              required
              label="Password"
              placeholder="Your password"
              {...form.getInputProps('password')}
              error={form.errors.password}
            />
            {!isLoginMode && (
              <PasswordInput
                required
                label="Confirm Password"
                placeholder="Confirm your password"
                {...form.getInputProps('confirmPassword')}
                error={form.errors.confirmPassword}
              />
            )}
          </Stack>

          {error && (
            <Alert title="Authentication Error" color="red" icon={<IconAlertCircle size="1rem" />} mt="lg" radius="md" withCloseButton onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Button
            type="submit"
            fullWidth
            mt="xl" // More space before main action button
            leftSection={isLoginMode ? <IconLogin size={rem(18)} /> : <IconUserPlus size={rem(18)} />}
            size="md"
          >
            {isLoginMode ? 'Sign In' : 'Create Account'}
          </Button>
        </form>

        <Divider label="Or" labelPosition="center" my="lg" />

        <Button
            fullWidth
            variant="outline" // Default is usually more subtle
            color="gray" // Standard for Google button
            leftSection={<IconBrandGoogle size={rem(18)} />}
            onClick={handleGoogleSignIn}
            disabled={formLoading}
            size="md"
        >
            Sign in with Google
        </Button>
      </Paper>
    </Container>
  );
};

export default LoginPage;
```
