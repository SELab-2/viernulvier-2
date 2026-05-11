/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable no-undef */
import '@testing-library/jest-dom/jest-globals'
import '@testing-library/jest-dom'
import { TextDecoder, TextEncoder } from 'util'
import './i18n'

global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder as typeof global.TextDecoder

process.env.PUBLIC_API_KEY = process.env.PUBLIC_API_KEY ?? 'test-api-key'

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
