/* eslint-disable no-undef */
import '@testing-library/jest-dom/jest-globals'
import '@testing-library/jest-dom'
import { TextDecoder, TextEncoder } from 'util'
import './i18n'

global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder as typeof global.TextDecoder

process.env.PUBLIC_API_KEY = process.env.PUBLIC_API_KEY ?? 'test-api-key'

// Mock axios to prevent XMLHttpRequest errors in tests
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    get: jest.fn().mockResolvedValue({ data: {} }),
    post: jest.fn().mockResolvedValue({ data: {} }),
    put: jest.fn().mockResolvedValue({ data: {} }),
    patch: jest.fn().mockResolvedValue({ data: {} }),
    delete: jest.fn().mockResolvedValue({ data: {} }),
    request: jest.fn().mockResolvedValue({ data: {} }),
    interceptors: {
      request: { use: jest.fn(), eject: jest.fn() },
      response: { use: jest.fn(), eject: jest.fn() },
    },
  })),
  isAxiosError: jest.fn(() => false),
}))

class IntersectionObserverMock implements IntersectionObserver {
  scrollMargin: string = ''
  readonly root: Element | Document | null = null
  readonly rootMargin = ''
  readonly thresholds: readonly number[] = []
  disconnect = () => {}
  observe = () => {}
  takeRecords = () => []
  unobserve = () => {}
}
Object.assign(global, { IntersectionObserver: IntersectionObserverMock })

class ResizeObserverMock implements ResizeObserver {
  disconnect = () => {}
  observe = () => {}
  unobserve = () => {}
}
Object.assign(global, { ResizeObserver: ResizeObserverMock })

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  configurable: true,
  value: jest.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

Object.defineProperty(window, 'scrollTo', {
  writable: true,
  configurable: true,
  value: jest.fn(),
})
