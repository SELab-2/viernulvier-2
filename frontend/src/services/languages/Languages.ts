import type { Language, LanguageListResponse } from '../../types/Languages'
import { api } from '../Api'
import { buildListParams } from '../ApiParams'
import type { GetLanguagesOptions } from './LanguageOptions'

/**
 * Retrieve a single language by its ISO code.
 *
 * This sends a `GET /languages/:code/` request to the backend and returns the
 * response payload exactly as received.
 *
 * @param code The ISO code of the language that should be fetched.
 * @returns A promise that resolves to the language data returned by the API.
 *
 * @example
 * const language = await getLanguage('nl');
 *
 * @throws {ApiError} When the request fails.
 */
export const getLanguage = async (code: string): Promise<Language> => {
  const res = await api.get<Language>(`/languages/${code}/`)
  return res.data
}

/**
 * Retrieve a list of languages with optional pagination and filtering.
 *
 * This sends a `GET /languages/` request. The `options` object is translated
 * into query parameters like this:
 * - `page` -> `page`
 * - `pageSize` -> `page_size`
 * - `filters` -> each filter key is forwarded directly as a query parameter
 *
 * Supported language-specific filter fields currently include:
 * - `code`: filter by ISO language code (case-insensitive on backend)
 * - `name`: filter by language name
 * - `is_active`: filter by active status
 *
 * In addition, all API list endpoints support these shared query parameters:
 * - `search`: free-text backend search
 * - `ordering`: backend ordering instruction, for example `code` or `-code`
 * - `external_id`: external identifier, for example `api/v1/languages/nl`
 *
 * @param options Optional settings for pagination and filtering.
 * @param options.page The page number to request.
 * @param options.pageSize The amount of items per page.
 * @param options.filters The filter values to apply to the request.
 * @returns A promise that resolves to the API response data, usually a paginated list.
 *
 * @example
 * const languages = await getLanguages();
 *
 * @example
 * const languages = await getLanguages({
 *   page: 1,
 *   pageSize: 20,
 *   filters: {
 *     code: 'nl',
 *     is_active: true,
 *     ordering: 'name',
 *   },
 * });
 *
 * @throws {ApiError} When the request fails.
 */
export const getLanguages = async (
  options?: GetLanguagesOptions,
): Promise<LanguageListResponse> => {
  const res = await api.get<LanguageListResponse>('/languages/', {
    params: buildListParams(options),
  })
  return res.data
}
