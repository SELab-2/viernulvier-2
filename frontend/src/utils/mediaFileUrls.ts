const isAbsoluteUrl = (value: string) => /^https?:\/\//i.test(value)

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
