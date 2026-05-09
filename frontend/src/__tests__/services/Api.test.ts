import { describe, expect, it, jest } from '@jest/globals'
import { AxiosHeaders } from 'axios'

import i18n from '../../i18n'
import { api } from '../../services/Api'
import { normalizeApiError } from '../../services/ApiErrorMapper'

jest.mock('../../services/ApiErrorMapper', () => ({
  normalizeApiError: jest.fn(),
}))

const mockedNormalizeApiError = normalizeApiError as jest.MockedFunction<typeof normalizeApiError>

describe('api', () => {
  it('configures baseURL and JSON/API key headers', () => {
    expect(api.defaults.baseURL).toBe('/api/v1')
    expect(api.defaults.headers['Content-Type']).toBe('application/json')
    expect(api.defaults.headers['X-API-Key']).toBeDefined()
  })

  it('adds Accept-Language from the active i18n language', async () => {
    await i18n.changeLanguage('en-US')

    const requestInterceptor = (api.interceptors.request as unknown as { handlers: unknown[] })
      .handlers[0] as {
      fulfilled: (config: { headers: AxiosHeaders }) => { headers: AxiosHeaders }
    }

    const config = { headers: new AxiosHeaders() }
    const nextConfig = requestInterceptor.fulfilled(config)

    expect(nextConfig.headers.get('Accept-Language')).toBe('en')
  })

  it('passes successful responses through unchanged', () => {
    const responseInterceptor = (api.interceptors.response as unknown as { handlers: unknown[] })
      .handlers[0] as {
      fulfilled: <T>(response: T) => T
    }
    const response = { status: 200, data: { ok: true } }

    expect(responseInterceptor.fulfilled(response)).toBe(response)
  })

  it('normalizes failed responses before rejecting', async () => {
    const responseInterceptor = (api.interceptors.response as unknown as { handlers: unknown[] })
      .handlers[0] as {
      rejected: (error: unknown) => Promise<never>
    }

    const axiosError = { isAxiosError: true, response: { status: 500 } }
    const normalizedError = new Error('normalized')
    mockedNormalizeApiError.mockReturnValueOnce(normalizedError)

    await expect(responseInterceptor.rejected(axiosError)).rejects.toBe(normalizedError)
    expect(mockedNormalizeApiError).toHaveBeenCalledTimes(1)
    expect(mockedNormalizeApiError.mock.calls[0][0]).toBe(axiosError)

    const isAxiosErrorPredicate = mockedNormalizeApiError.mock.calls[0][1] as (
      value: unknown,
    ) => boolean
    expect(isAxiosErrorPredicate({ isAxiosError: true })).toBe(true)
    expect(isAxiosErrorPredicate(new Error('plain'))).toBe(false)
  })
})
