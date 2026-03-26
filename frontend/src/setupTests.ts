/* eslint-disable no-undef */
import '@testing-library/jest-dom'
import { TextDecoder, TextEncoder } from 'util'

global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder as typeof global.TextDecoder

process.env.VITE_PUBLIC_API_KEY = process.env.VITE_PUBLIC_API_KEY ?? 'test-api-key'
