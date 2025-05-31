```tsx
import React from 'react';
import { Container, Title, Text, Button, Group, Paper, ThemeIcon } from '@mantine/core';
import { Link } from 'react-router-dom';
import { IconError404, IconHome } from '@tabler/icons-react';

const NotFoundPage: React.FC = () => {
  return (
    <Container size="md" py="xl" style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
       <Paper shadow="md" p="xl" radius="md" withBorder style={{ textAlign: 'center' }}>
        <ThemeIcon variant="light" color="noahBlue" size={120} radius={120} mx="auto">
            <IconError404 size={80} stroke={1.5} />
        </ThemeIcon>
        <Title order={1} mt="xl" mb="md" ff={'Greycliff CF, sans-serif'}>Something is not right...</Title>
        <Text c="dimmed" size="lg" mb="xl">
          The page you are looking for couldn't be found.
          It might have been moved or deleted, or perhaps you mistyped the address.
        </Text>
        <Group justify="center">
          <Button component={Link} to="/" size="md" leftSection={<IconHome size="1.1rem" />}>
            Go back to Home
          </Button>
        </Group>
      </Paper>
    </Container>
  );
};

export default NotFoundPage;
```
