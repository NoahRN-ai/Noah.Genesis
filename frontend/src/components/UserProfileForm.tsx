import React, { useEffect } from 'react';
import { useForm, zodResolver } from '@mantine/form';
import { z } from 'zod';
import { TextInput, Button, Stack, Paper, Title, Text, Select, Switch, Group, LoadingOverlay, Alert } from '@mantine/core';
import { IconDeviceFloppy, IconAlertCircle } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { UserProfileData, UserProfileUpdatePayload, UserRole } from '../types/api';
import { updateUserProfile } from '../services/userProfileApiService';
import { useAuth } from '../hooks/useAuth'; // To get current user ID

// Define Zod schema for form validation
const userProfileFormSchema = z.object({
  displayName: z.string().min(2, { message: 'Display name must be at least 2 characters' }).max(50, {message: 'Display name too long'}).optional().or(z.literal('')),
  preferences: z.object({
    summaryLength: z.enum(['concise', 'normal', 'detailed']).default('normal'),
    enableEmailNotifications: z.boolean().default(true),
    // Add more preference fields here as needed
  }).default({ summaryLength: 'normal', enableEmailNotifications: true }),
});

type UserProfileFormValues = z.infer<typeof userProfileFormSchema>;

interface UserProfileFormProps {
  initialProfileData: UserProfileData | null;
  onProfileUpdate?: (updatedProfile: UserProfileData) => void;
  isLoadingData: boolean;
  isOwnProfile: boolean; // To disable editing certain fields if not own profile (e.g. role)
}

export const UserProfileForm: React.FC<UserProfileFormProps> = ({
  initialProfileData,
  onProfileUpdate,
  isLoadingData,
  isOwnProfile,
}) => {
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [submitError, setSubmitError] = React.useState<string | null>(null);
  const { currentUser } = useAuth();

  const form = useForm<UserProfileFormValues>({
    validate: zodResolver(userProfileFormSchema),
    initialValues: {
      displayName: initialProfileData?.displayName || '',
      preferences: {
        summaryLength: initialProfileData?.preferences?.summaryLength || 'normal',
        enableEmailNotifications: initialProfileData?.preferences?.enableEmailNotifications === undefined ? true : initialProfileData.preferences.enableEmailNotifications,
      },
    },
  });

  useEffect(() => {
    if (initialProfileData) {
      form.setValues({
        displayName: initialProfileData.displayName || '',
        preferences: {
          summaryLength: initialProfileData.preferences?.summaryLength || 'normal',
          enableEmailNotifications: initialProfileData.preferences?.enableEmailNotifications === undefined ? true : initialProfileData.preferences.enableEmailNotifications,
        },
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialProfileData]); // form object is stable, no need to include it in deps array

  const handleSubmit = async (values: UserProfileFormValues) => {
    if (!initialProfileData || !currentUser || !isOwnProfile) { // Prevent submission if no data or not allowed
      notifications.show({ title: 'Error', message: 'Cannot update profile at this time.', color: 'noahRed'});
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    const updatePayload: UserProfileUpdatePayload = {
      display_name: values.displayName,
      preferences: values.preferences,
    };

    try {
      // Ensure updateUserProfile is defined and correctly imported
      // For now, assuming it's correctly set up in services.
      const updatedProfile = await updateUserProfile(initialProfileData.user_id, updatePayload);
      notifications.show({
        title: 'Profile Updated',
        message: 'Your profile has been successfully updated.',
        color: 'noahGreen',
        icon: <IconDeviceFloppy />,
      });
      if (onProfileUpdate) {
        onProfileUpdate(updatedProfile);
      }
      form.resetDirty(values); // Reset dirty state with new values
    } catch (error: any) {
      const message = error.message || 'Failed to update profile. Please try again.';
      setSubmitError(message);
      notifications.show({
        title: 'Update Failed',
        message,
        color: 'noahRed',
        icon: <IconAlertCircle />,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Paper shadow="none" p={0} pos="relative"> {/* Remove Paper's default shadow if page has one */}
      <LoadingOverlay visible={isLoadingData || isSubmitting} overlayProps={{ radius: "sm", blur: 2 }} />
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Stack gap="lg">
          <TextInput
            label="Display Name"
            placeholder="Your preferred display name"
            {...form.getInputProps('displayName')}
            disabled={!isOwnProfile}
          />
          <TextInput
            label="User ID (Firebase UID)"
            value={initialProfileData?.user_id || 'N/A'}
            disabled
          />
           <TextInput
            label="Email"
            value={currentUser?.email || initialProfileData?.user_id || 'N/A'} // Display current user email if matches
            disabled
          />
          <TextInput
            label="Role"
            value={initialProfileData?.role || 'N/A'}
            disabled // Role typically not user-editable
            description="Your role in the Noah.AI system."
          />

          <Title order={4} mt="md">Preferences</Title>
          <Select
            label="LLM Summary Length"
            placeholder="Choose summary length preference"
            data={[
              { value: 'concise', label: 'Concise (Quick overview)' },
              { value: 'normal', label: 'Normal (Standard detail)' },
              { value: 'detailed', label: 'Detailed (In-depth information)' },
            ]}
            {...form.getInputProps('preferences.summaryLength')}
            disabled={!isOwnProfile}
          />
          <Switch
            label="Enable Email Notifications"
            {...form.getInputProps('preferences.enableEmailNotifications', { type: 'checkbox' })}
            disabled={!isOwnProfile}
            mt="xs"
          />

          {/* Add more preference fields here following the pattern above */}

          {submitError && (
            <Alert title="Error" color="noahRed" icon={<IconAlertCircle size="1rem" />} withCloseButton onClose={() => setSubmitError(null)}>
              {submitError}
            </Alert>
          )}
          {isOwnProfile && (
            <Group justify="flex-end" mt="xl">
              <Button
                type="submit"
                leftSection={<IconDeviceFloppy size="1rem" />}
                loading={isSubmitting}
                disabled={!form.isDirty()}
              >
                Save Changes
              </Button>
            </Group>
          )}
        </Stack>
      </form>
    </Paper>
  );
};
