export function getLocalizedValue(
  obj: Record<string, string> | null | undefined,
  lang = 'nl',
): string {
  if (!obj || typeof obj !== 'object') return ''
  return obj[lang] || Object.values(obj)[0] || ''
}
