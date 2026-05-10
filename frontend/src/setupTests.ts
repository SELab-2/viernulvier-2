/* eslint-disable no-undef */
import '@testing-library/jest-dom/jest-globals'
import '@testing-library/jest-dom'
import { TextDecoder, TextEncoder } from 'util'
import './i18n'

global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder as typeof global.TextDecoder

process.env.PUBLIC_API_KEY = process.env.PUBLIC_API_KEY ?? 'test-api-key'

// Mock axios to prevent XMLHttpRequest errors in tests
jest.mock('axios', () => {
  const handlers = { request: [], response: [] }

  class AxiosHeaders {
    private headers: { [key: string]: string } = {}

    set(key: string, value: string) {
      this.headers[key] = value
      return this
    }

    get(key: string): string | undefined {
      return this.headers[key]
    }
  }

  return {
    create: jest.fn(() => ({
      defaults: {
        baseURL: '/api/v1',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': process.env.PUBLIC_API_KEY ?? 'test-api-key',
        },
      },
      get: jest.fn().mockResolvedValue({ data: {} }),
      post: jest.fn().mockResolvedValue({ data: {} }),
      put: jest.fn().mockResolvedValue({ data: {} }),
      patch: jest.fn().mockResolvedValue({ data: {} }),
      delete: jest.fn().mockResolvedValue({ data: {} }),
      request: jest.fn().mockResolvedValue({ data: {} }),
      interceptors: {
        request: {
          use: jest.fn((fulfilled) => {
            handlers.request.push({ fulfilled })
          }),
          handlers: handlers.request,
          eject: jest.fn(),
        },
        response: {
          use: jest.fn((fulfilled, rejected) => {
            handlers.response.push({ fulfilled, rejected })
          }),
          handlers: handlers.response,
          eject: jest.fn(),
        },
      },
    })),
    AxiosHeaders,
    isAxiosError: jest.fn((value: unknown) => {
      return typeof value === 'object' && value !== null && value.isAxiosError === true
    }),
  }
})

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
