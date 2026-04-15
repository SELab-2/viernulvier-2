const js = require('@eslint/js')
const globals = require('globals')
const tsPlugin = require('@typescript-eslint/eslint-plugin')
const tsParser = require('@typescript-eslint/parser')
const react = require('eslint-plugin-react')
const reactHooks = require('eslint-plugin-react-hooks')
const reactRefresh = require('eslint-plugin-react-refresh')
const prettier = require('eslint-plugin-prettier')
const prettierConfig = require('eslint-config-prettier')
const importPlugin = require('eslint-plugin-import')

const reactRefreshPlugin = reactRefresh.default ?? reactRefresh
const tsRules = tsPlugin.configs['recommended'].rules

module.exports = [
  js.configs.recommended,
  prettierConfig,

  // Ignored paths
  {
    ignores: [
      'dist/**',
      'build/**',
      'out/**',
      'node_modules/**',
      'coverage/**',
      '.cache/**',
      '**/*.d.ts',
      '*.config.js',
      '*.config.cjs',
      '*.config.mjs',
      'vite.config.*',
      'vitest.config.*',
      'jest.config.*',
      'tailwind.config.*',
      'postcss.config.*',
    ],
  },

  // TypeScript + React files
  {
    files: ['**/*.{ts,tsx}'],

    languageOptions: {
      parser: tsParser,
      parserOptions: {
        project: ['./tsconfig.json', './tsconfig.jest.json'],
        tsconfigRootDir: __dirname,
      },
      globals: {
        ...globals.browser,
        ...globals.es2021,
        ...globals.jest,
        process: 'readonly',
        __dirname: 'readonly',
        __filename: 'readonly',
      },
    },

    settings: {
      react: { version: 'detect' },
      'import/resolver': {
        typescript: { alwaysTryTypes: true },
        node: { extensions: ['.ts', '.tsx', '.js', '.jsx'] },
      },
    },

    plugins: {
      '@typescript-eslint': tsPlugin,
      react,
      'react-hooks': reactHooks,
      'react-refresh': reactRefreshPlugin,
      prettier,
      import: importPlugin,
    },

    rules: {
      // TypeScript
      ...tsRules,

      '@typescript-eslint/no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_', ignoreRestSiblings: true },
      ],
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-non-null-assertion': 'off',
      '@typescript-eslint/consistent-type-imports': [
        'error',
        { prefer: 'type-imports', fixStyle: 'inline-type-imports' },
      ],
      '@typescript-eslint/consistent-type-exports': 'error',
      '@typescript-eslint/no-import-type-side-effects': 'error',
      '@typescript-eslint/array-type': ['error', { default: 'array-simple' }],
      '@typescript-eslint/prefer-optional-chain': 'warn',
      '@typescript-eslint/prefer-nullish-coalescing': 'off',
      '@typescript-eslint/no-unnecessary-type-assertion': 'off', // enable with project
      '@typescript-eslint/no-floating-promises': 'off', // enable with project
      '@typescript-eslint/await-thenable': 'off', // enable with project

      // React
      ...react.configs.recommended.rules,
      ...react.configs['jsx-runtime'].rules,
      ...reactHooks.configs.recommended.rules,

      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'error',

      'react/prop-types': 'off', // TS handles this
      'react/display-name': 'warn',
      'react/no-array-index-key': 'off',
      'react/no-unused-prop-types': 'warn',
      'react/self-closing-comp': 'error',
      'react/jsx-curly-brace-presence': ['error', { props: 'never', children: 'never' }],
      'react/jsx-boolean-value': ['error', 'never'],
      'react/jsx-no-useless-fragment': ['error', { allowExpressions: true }],
      'react/jsx-pascal-case': 'error',
      'react/hook-use-state': 'warn',
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],

      // Imports
      'import/no-duplicates': ['error', { 'prefer-inline': true }],
      'import/no-cycle': 'warn',
      'import/no-self-import': 'error',
      'import/order': [
        'warn',
        {
          groups: [
            'builtin',
            'external',
            'internal',
            ['parent', 'sibling'],
            'index',
            'object',
            'type',
          ],
          'newlines-between': 'always',
          alphabetize: { order: 'asc', caseInsensitive: true },
        },
      ],

      // General JavaScript quality
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'no-debugger': 'error',
      'no-alert': 'warn',
      'no-var': 'error',
      'prefer-const': 'error',
      'prefer-template': 'error',
      'prefer-destructuring': ['warn', { object: true, array: false }],
      'object-shorthand': 'error',
      'no-useless-rename': 'error',
      'no-duplicate-imports': 'off', // handled by import/no-duplicates
      'no-shadow': 'off', // use @typescript-eslint/no-shadow instead
      '@typescript-eslint/no-shadow': 'off',
      'no-restricted-syntax': [
        'error',
        {
          selector: "JSXAttribute[name.name='style']",
          message: 'Use MUI sx or theme utilities instead of inline style props.',
        },
      ],
      eqeqeq: ['error', 'always', { null: 'ignore' }],
      'no-implicit-coercion': ['warn', { boolean: false }],
      'no-nested-ternary': 'off',
      'no-unneeded-ternary': 'error',
      'no-else-return': ['error', { allowElseIf: false }],
      'consistent-return': 'off',
      curly: ['error', 'all'],
      'spaced-comment': ['error', 'always', { markers: ['/'] }],
      yoda: 'error',

      // Prettier
      'prettier/prettier': 'error',
    },
  },

  // Plain JS files (scripts, configs accidentally linted)
  {
    files: ['**/*.{js,mjs,cjs}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: { ...globals.node, ...globals.browser },
    },
    rules: {
      'no-var': 'error',
      'prefer-const': 'error',
      'no-console': 'off',
    },
  },

  // Test files - relax certain rules
  {
    files: [
      '**/*.test.{ts,tsx}',
      '**/*.spec.{ts,tsx}',
      '**/__tests__/**/*.{ts,tsx}',
      '**/test/**/*.{ts,tsx}',
    ],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-non-null-assertion': 'off',
      'no-console': 'off',
      'react/display-name': 'off',
    },
  },
]
