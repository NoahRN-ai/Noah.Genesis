import React, { useState, useEffect } from 'react';
import { useParams, Navigate, Link } from 'react-router-dom';
import { Container, Paper, Title, Loader, Center, Alert, Breadcrumbs, Anchor, Text, Space, Group, ThemeIcon } from '@mantine/core';
import { IconUserCircle, IconHome, IconAlertCircle } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications'; // Added for consistency
import { useAuth } from '../hooks/useAuth';
import { getUserProfile } from '../services/userProfileApiService';
import { UserProfileData } from '../types/api';
import { UserProfileForm } from '../components/UserProfileForm';

const UserProfilePage: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const { currentUser, isLoading: authIsLoading, isInitialized } = useAuth();

  const [profileData, setProfileData] = useState<UserProfileData | null>(null);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const effectiveUserId = userId === 'me' && currentUser ? currentUser.uid : userId;
  const isOwnProfile = currentUser?.uid === effectiveUserId;

  useEffect(() => {
    if (!isInitialized || authIsLoading) {
      return;
    }
    if (!effectiveUserId) {
      setError("User ID not found. Cannot load profile.");
      setIsLoadingData(false);
      return;
    }
    if (!currentUser) { // Should be caught by isInitialized check if currentUser is null post-init
      setError("Authentication required to view profiles.");
      setIsLoadingData(false);
      return;
    }

    const fetchProfile = async () => {
      setIsLoadingData(true);
      setError(null);
      try {
        // Ensure getUserProfile is defined and correctly imported
        // For now, assuming it's correctly set up in services.
        const data = await getUserProfile(effectiveUserId);
        setProfileData(data);
      } catch (err: any) {
        console.error(`Failed to fetch profile for ${effectiveUserId}:`, err);
        const errorMessage = err.response?.data?.detail || err.message || 'Could not load user profile.';
        setError(errorMessage);
        notifications.show({ title: 'Profile Load Error', message: errorMessage, color: 'noahRed' });
      } finally {
        setIsLoadingData(false);
      }
    };

    fetchProfile();
  }, [effectiveUserId, currentUser, isInitialized, authIsLoading]); // Added missing dependencies

  if (authIsLoading || (!isInitialized && isLoadingData)) { // Initial loading checks for auth and page data
    return <Center style={{ height: '50vh' }}><Loader size="lg" /></Center>;
  }

  if (!currentUser && isInitialized) { // If auth is initialized and still no user, redirect.
    // This case implies that `effectiveUserId` might also be undefined if `userId` was 'me'.
    // Or if `userId` was explicit but user logs out in another tab.
    notifications.show({ title: 'Authentication Required', message: 'Please log in to view this page.', color: 'noahRed' });
    return <Navigate to="/login" replace />;
  }

  if (error && !isLoadingData) { // Display error if fetching failed after auth check
    return (
      <Container size="md" py="xl">
        <Alert title="Error Loading Profile" color="noahRed" icon={<IconAlertCircle />}>
          {error} Please try again or contact support if the issue persists.
        </Alert>
      </Container>
    );
  }

  // This specific loader handles the case where auth is resolved, but profile data is still loading.
  if (isLoadingData) {
    return <Center style={{ height: '50vh' }}><Loader size="lg" /></Center>;
  }

  if (!profileData) { // If loading is finished, no error, but no profile data (e.g., 404 from API)
    return (
      <Container size="md" py="xl">
        <Alert title="Profile Not Found" color="orange" icon={<IconAlertCircle />}>
          The user profile for ID '{effectiveUserId}' could not be found.
          It may not exist or you may not have permission to view it.
          {isOwnProfile && effectiveUserId && !profileData ?
           " Your profile might not have been fully created in the application database yet." : ""}
        </Alert>
      </Container>
    );
  }

  const breadcrumbItems = [
    { title: 'Home', href: '/' },
    { title: 'User Profile', href: `/profile/${effectiveUserId}` },
  ].map((item, index) => (
    <Anchor component={Link} to={item.href} key={index}>
      {item.title}
    </Anchor>
  ));

  return (
    <Container size="md" py="xl">
      <Breadcrumbs mb="xl">{breadcrumbItems}</Breadcrumbs>
      <Paper shadow="sm" p="xl" withBorder radius="md">
        <Group mb="lg">
          <ThemeIcon variant="light" size="xl" radius="md" color="noahBlue">
            <IconUserCircle size="2rem" />
          </ThemeIcon>
          <Title order={2}>User Profile</Title>
        </Group>
        {isOwnProfile ? (
          <Text c="dimmed" mb="lg">Manage your display name and application preferences.</Text>
        ) : (
          <Text c="dimmed" mb="lg">Viewing profile for {profileData.displayName || profileData.user_id}.</Text>
        )}
        <UserProfileForm
          initialProfileData={profileData}
          isLoadingData={isLoadingData} // This reflects the profile data loading, could be false here.
                                       // The form's internal overlay is for its own submission state mainly.
          isOwnProfile={isOwnProfile}
          onProfileUpdate={(updatedData) => {
            setProfileData(updatedData);
            // Optional: show page-level notification if desired, though form has its own.
            // notifications.show({
            //     title: 'Profile Updated (Page)',
            //     message: 'Local profile view has been refreshed.',
            //     color: 'noahGreen',
            // });
          }}
        />
      </Paper>
      <Space h="xl" />
    </Container>
  );
};

export default UserProfilePage;
