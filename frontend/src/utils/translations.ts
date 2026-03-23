export function getTranslatedRecord(
  record: Record<string, string> | null | undefined,
  language: string,
  fallback: string | null = null,
): string {
  if (!fallback) {
    fallback = ''
  }

  if (!record || Object.keys(record).length === 0) {
    return fallback
  }

  const translation = record[language]
  if (translation) {
    return translation
  }

  return fallback
}
