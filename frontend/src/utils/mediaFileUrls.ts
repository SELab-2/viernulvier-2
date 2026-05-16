/**
 * Checks whether a given string is an absolute HTTP or HTTPS URL.
 *
 * @param value The URL string to check
 * @returns `true` if the value starts with http:// or https://
 */
const isAbsoluteUrl = (value: string) => /^https?:\/\//i.test(value)

/**
 * Converts a media file URL into a public, frontend-safe URL.
 *
 * Rules:
 * - If the URL is absolute (http/https), it is converted to a same-origin URL
 *   using `window.location.origin`, preserving path, query, and hash.
 * - If the URL is already root-relative (starts with "/"), it is returned as-is.
 * - If the URL is relative (no leading slash), a "/" is prepended.
 * - If the URL is falsy, it is returned unchanged.
 *
 * @param fileUrl Raw media file URL from backend or CMS
 * @returns A normalized public URL usable in the browser
 */
export const getPublicMediaFileUrl = (fileUrl: string): string => {
  if (!fileUrl) {
    return fileUrl
  }

  if (isAbsoluteUrl(fileUrl)) {
    try {
      const url = new URL(fileUrl)
      return `${window.location.origin}${url.pathname}${url.search}${url.hash}`
    } catch {
      return fileUrl
    }
  }

  if (fileUrl.startsWith('/')) {
    return fileUrl
  }

  return `/${fileUrl}`
}
