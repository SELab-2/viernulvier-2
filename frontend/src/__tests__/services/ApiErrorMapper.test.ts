import { ApiError } from '../../services/ApiTypes'
import { normalizeApiError } from '../../services/ApiErrorMapper'
import i18n from '../../i18n'

describe('normalizeApiError', () => {
  const isAxiosError = (error: unknown) => {
    return Boolean((error as { isAxiosError?: boolean })?.isAxiosError)
  }

  beforeEach(async () => {
    await i18n.changeLanguage('en')
  })

  it.each([
    [400, 'Invalid request parameters.'],
    [401, 'Not authenticated. Please log in.'],
    [403, 'You do not have permission to perform this action.'],
    [404, 'The requested resource was not found.'],
    [500, 'An internal server error occurred. Please try again later.'],
  ])('maps HTTP %i to ApiError with message', (status, expectedMessage) => {
    const result = normalizeApiError(
      {
        isAxiosError: true,
        response: { status },
      },
      isAxiosError,
    )

    expect(result).toBeInstanceOf(ApiError)
    expect(result).toMatchObject({ status, message: expectedMessage })
  })

  it('maps unknown HTTP statuses to a generic status message', () => {
    const result = normalizeApiError(
      {
        isAxiosError: true,
        response: { status: 502 },
      },
      isAxiosError,
    )

    expect(result).toBeInstanceOf(ApiError)
    expect(result).toMatchObject({
      status: 502,
      message: 'Request failed with status 502.',
    })
  })

  it('maps response-less Axios errors to network status 0', () => {
    const result = normalizeApiError(
      {
        isAxiosError: true,
        request: {},
      },
      isAxiosError,
    )

    expect(result).toBeInstanceOf(ApiError)
    expect(result).toMatchObject({
      status: 0,
      message: 'A network error occurred. Please check your connection.',
    })
  })

  it('returns Dutch messages when active language is nl', async () => {
    await i18n.changeLanguage('nl')

    const result = normalizeApiError(
      {
        isAxiosError: true,
        response: { status: 404 },
      },
      isAxiosError,
    )

    expect(result).toBeInstanceOf(ApiError)
    expect(result).toMatchObject({
      status: 404,
      message: 'De gevraagde resource werd niet gevonden.',
    })
  })

  it('returns non-Axios errors unchanged', () => {
    const error = new Error('boom')
    const result = normalizeApiError(error, isAxiosError)
    expect(result).toBe(error)
  })
})
