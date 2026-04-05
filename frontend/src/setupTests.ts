/* eslint-disable no-undef */
import '@testing-library/jest-dom'
import { TextDecoder, TextEncoder } from 'util'

global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder as typeof global.TextDecoder

process.env.VITE_PUBLIC_API_KEY = process.env.VITE_PUBLIC_API_KEY ?? 'test-api-key'

class IntersectionObserverMock implements IntersectionObserver {
  readonly root: Element | Document | null = null
  readonly rootMargin = ''
  readonly thresholds: ReadonlyArray<number> = []
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
