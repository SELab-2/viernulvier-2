/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable no-undef */
import '@testing-library/jest-dom/jest-globals'
import '@testing-library/jest-dom'
import { TextDecoder, TextEncoder } from 'util'
import './i18n'

global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder as typeof global.TextDecoder

process.env.PUBLIC_API_KEY = process.env.PUBLIC_API_KEY ?? 'test-api-key'

// Mock axios to prevent XMLHttpRequest errors in tests
type InterceptorEntry = {
  fulfilled?: (value: unknown) => unknown
  rejected?: (error: unknown) => unknown
}

jest.mock('axios', () => {
  const handlers: { request: InterceptorEntry[]; response: InterceptorEntry[] } = {
    request: [],
    response: [],
  }

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
          use: jest.fn((fulfilled: (value: unknown) => unknown) => {
            handlers.request.push({ fulfilled })
          }),
          handlers: handlers.request,
          eject: jest.fn(),
        },
        response: {
          use: jest.fn(
            (fulfilled: (value: unknown) => unknown, rejected?: (error: unknown) => unknown) => {
              handlers.response.push({ fulfilled, rejected })
            },
          ),
          handlers: handlers.response,
          eject: jest.fn(),
        },
      },
    })),
    AxiosHeaders,
    isAxiosError: jest.fn((value: unknown) => {
      if (typeof value === 'object' && value !== null) {
        const v = value as Record<string, unknown>
        return v.isAxiosError === true
      }
      return false
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

// Suppress jsdom XHR AggregateError noise in test output (these are harmless
// network errors triggered by environment helpers; they clutter CI logs).
const originalConsoleError = console.error
console.error = (...args: unknown[]) => {
  const first = args[0]
  if (first && typeof first === 'object' && 'type' in (first as any)) {
    const maybe = first as any
    if (maybe.type === 'XMLHttpRequest') {
      return
    }
  }
  originalConsoleError(...(args as [any, ...any[]]))
}
