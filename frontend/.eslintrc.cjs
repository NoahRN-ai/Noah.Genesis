```javascript
module.exports = {
  root: true,
  env: { browser: true, es2020: true, node: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime', // For the new JSX transform
    'plugin:react-hooks/recommended',
    'plugin:prettier/recommended', // This must be the last extension
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs', 'vite.config.ts', 'node_modules', 'coverage', 'public'],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    project: ['./tsconfig.json', './tsconfig.node.json'], // For type-aware linting rules
    // tsconfigRootDir: __dirname, // Usually not needed if tsconfig paths are relative to this eslintrc
  },
  plugins: [
    '@typescript-eslint',
    'react',
    'react-hooks',
    'react-refresh',
    'prettier'
  ],
  settings: {
    react: {
      version: 'detect', // Automatically detect the React version
    },
  },
  rules: {
    'prettier/prettier': ['warn', {}, { usePrettierrc: true }], // Ensure Prettier config is used
    'react/prop-types': 'off', // Disabled as TypeScript handles prop types
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-unused-vars': [
      'warn',
      {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        caughtErrorsIgnorePattern: '^_'
      }
    ],
    '@typescript-eslint/no-explicit-any': 'warn', // Discourage 'any' but allow for MVP velocity
    // Consider enabling stricter rules later or based on project needs:
    // '@typescript-eslint/explicit-module-boundary-types': 'off', // Could be 'warn' or 'error'
    // '@typescript-eslint/no-floating-promises': 'warn',
  },
};
```
