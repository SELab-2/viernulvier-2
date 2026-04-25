module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', { tsconfig: 'tsconfig.jest.json' }],
  },
  moduleNameMapper: {
    '^react-pdf$': '<rootDir>/src/__mocks__/react-pdf.ts',
  },
  moduleFileExtensions: ['ts', 'tsx', 'js'],
}
