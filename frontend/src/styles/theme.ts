```typescript
import { MantineColorsTuple, MantineThemeOverride, createTheme, rem } from '@mantine/core';

const noahYellow: MantineColorsTuple = [
  '#FFF8E1', '#FFECB3', '#FFE082', '#FFD54F', '#FFCA28',
  '#FFC107', '#FFB300', '#FFA000', '#FF8F00', '#FF6F00',
];
const noahBlue: MantineColorsTuple = [
  '#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6', '#42A5F5',
  '#2196F3', '#1E88E5', '#1976D2', '#1565C0', '#0D47A1',
];
const noahGreen: MantineColorsTuple = [
  '#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784', '#66BB6A',
  '#4CAF50', '#43A047', '#388E3C', '#2E7D32', '#1B5E20',
];
const noahRed: MantineColorsTuple = [
  '#FFEBEE', '#FFCDD2', '#EF9A9A', '#E57373', '#EF5350',
  '#F44336', '#E53935', '#D32F2F', '#C62828', '#B71C1C',
];
const noahDarkGray: MantineColorsTuple = [
  '#FAFAFA', '#F0F0F0', '#E0E0E0', '#BDBDBD', '#757575',
  '#5F6368', '#4A4A4A', '#3A3A3A', '#2A2A2A', '#1A1A1A',
];

export const noahTheme: MantineThemeOverride = createTheme({
  fontFamily: 'Roboto, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif, Apple Color Emoji, Segoe UI Emoji',
  primaryColor: 'noahBlue',
  primaryShade: { light: 6, dark: 7 },
  white: '#FFFFFF',
  black: noahDarkGray[7], // Primary text color (strong dark gray)
  defaultRadius: 'md', // Slightly more rounded corners

  colors: {
    noahYellow, noahBlue, noahGreen, noahRed, noahDarkGray,
    // Use Mantine's standard names for semantic colors but point them to our tuples for consistency
    red: noahRed,
    green: noahGreen,
    // blue is already primary (noahBlue)
    yellow: noahYellow, // Can be used for warnings or accents
    gray: noahDarkGray, // Override default gray to use our neutral palette
  },
  headings: {
    fontFamily: 'Roboto, -apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif',
    fontWeight: '600',
    sizes: {
      h1: { fontSize: rem(32), lineHeight: '1.3', fontWeight: '700' },
      h2: { fontSize: rem(26), lineHeight: '1.35', fontWeight: '700' },
      h3: { fontSize: rem(22), lineHeight: '1.4', fontWeight: '600' },
    },
  },
  components: {
    Button: { defaultProps: { radius: 'sm' } },
    Paper: { defaultProps: { shadow: 'sm', radius: 'md', withBorder: true } }, // Added withBorder for subtle definition
    TextInput: { defaultProps: { radius: 'sm' } },
    PasswordInput: { defaultProps: { radius: 'sm' } },
    Select: { defaultProps: { radius: 'sm' } },
    Textarea: { defaultProps: { radius: 'sm' } },
    Modal: { defaultProps: { radius: 'md', shadow: 'lg' } },
    Alert: {
      styles: (theme, props) => ({
        message: {
          color: props.color ? theme.fn.themeColor(props.color, theme.colorScheme === 'dark' ? 0 : 8) : theme.black,
        },
        title: {
            color: props.color ? theme.fn.themeColor(props.color, theme.colorScheme === 'dark' ? 1 : 9) : theme.black,
        }
      })
    },
    Notification: {
      defaultProps: { radius: 'md' },
      styles: (theme) => ({
        root: { borderColor: theme.colors.noahDarkGray[2] },
        title: { color: theme.black, fontWeight: 600 },
        description: { color: theme.colors.noahDarkGray[6] },
      }),
    },
    Anchor: { defaultProps: (theme) => ({ color: theme.colors.noahBlue[theme.fn.primaryShade()] }) },
    AppShell: {
      styles: (theme) => ({
        main: {
          backgroundColor: theme.colorScheme === 'dark' ? theme.colors.noahDarkGray[9] : theme.colors.noahDarkGray[0],
          minHeight: 'calc(100vh - var(--app-shell-header-height, 0px) - var(--app-shell-footer-height, 0px))', // Ensure main fills height
        },
        header: {
          backgroundColor: theme.colorScheme === 'dark' ? theme.colors.noahDarkGray[8] : theme.white,
          borderBottom: `${rem(1)} solid ${theme.colorScheme === 'dark' ? theme.colors.noahDarkGray[7] : theme.colors.noahDarkGray[2]}`,
        },
        navbar: {
          backgroundColor: theme.colorScheme === 'dark' ? theme.colors.noahDarkGray[8] : theme.white,
          borderRight: `${rem(1)} solid ${theme.colorScheme === 'dark' ? theme.colors.noahDarkGray[7] : theme.colors.noahDarkGray[2]}`,
        }
      })
    }
  },
});
```
