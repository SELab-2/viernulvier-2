/**
 * Shared admin upload validation for image/media file inputs.
 *
 * Features
 * --------
 * - Restricts uploads to the MIME types defined via the input's `accept` attribute
 * - Validates both regular file selection and drag & drop uploads
 * - Clears previous Django admin validation errors when selecting a new file
 * - Prevents unsupported files from being attached to the form
 * - Displays user-friendly validation feedback directly in the Django admin UI
 *
 * Supported usage
 * ---------------
 * This script is intended to be reused across multiple Django admin forms
 * (e.g. tags, blogs, media files) by attaching it through the admin `Media`
 * class:
 *
 *     class Media:
 *         js = ("admin/js/media_file_upload.js",)
 *
 * Validation behaviour is automatically derived from the input's `accept`
 * attribute, making the script reusable without per-model customization.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Find all file inputs on the page.
  const fileInputs = document.querySelectorAll('input[type="file"]')

  if (!fileInputs.length) return

  /**
   * Maps file extensions to MIME types.
   *
   * The browser `accept` attribute may contain extensions instead of MIME
   * types, so we normalize everything to MIME types before validation.
   */
  const MIME_TYPE_BY_EXTENSION = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.webp': 'image/webp',
    '.pdf': 'application/pdf',
  }

  /**
   * Extract and normalize allowed MIME types from the input's `accept` attribute.
   */
  const getAllowedTypes = (fileInput) => {
    const accept = fileInput.getAttribute('accept') || ''

    return accept
      .split(',')
      .map((value) => value.trim().toLowerCase())
      .filter(Boolean)
      .map((value) => MIME_TYPE_BY_EXTENSION[value] || value)
  }

  /**
   * Convert MIME types into user-friendly labels for error messages.
   */
  const getAllowedLabel = (allowedTypes) => {
    const labels = []

    if (allowedTypes.includes('image/jpeg')) labels.push('JPG')
    if (allowedTypes.includes('image/png')) labels.push('PNG')
    if (allowedTypes.includes('image/webp')) labels.push('WEBP')
    if (allowedTypes.includes('application/pdf')) labels.push('PDF')

    return labels.join(', ')
  }

  /**
   * Remove previous validation errors from the admin form.
   *
   * This ensures old errors disappear immediately after selecting a new file.
   */
  const removeErrors = () => {
    document.querySelectorAll('.errorlist').forEach((el) => el.remove())
    document.querySelectorAll('.errornote').forEach((el) => el.remove())
    document.querySelectorAll('.errors').forEach((el) => el.classList.remove('errors'))
  }

  /**
   * Display a validation error in the standard Django admin style.
   */
  const showError = (fileInput, message) => {
    const formRow = fileInput.closest('.form-row')

    if (formRow) {
      formRow.classList.add('errors')

      const ul = document.createElement('ul')
      ul.className = 'errorlist'

      const li = document.createElement('li')
      li.textContent = message

      ul.appendChild(li)
      formRow.prepend(ul)
    }

    // Add the top-level admin error banner if not already present.
    const form = fileInput.closest('form')

    if (form && !form.querySelector('.errornote')) {
      const p = document.createElement('p')
      p.className = 'errornote'
      p.textContent = 'Please correct the error below.'

      form.prepend(p)
    }
  }

  /**
   * Check whether the uploaded file matches one of the allowed MIME types.
   */
  const isValidFile = (file, allowedTypes) => allowedTypes.includes(file.type)

  /**
   * Validate a file against the input's allowed MIME types.
   */
  const validateFile = (fileInput, file) => {
    const allowedTypes = getAllowedTypes(fileInput)

    // No restrictions configured → allow file.
    if (!allowedTypes.length || isValidFile(file, allowedTypes)) {
      return true
    }

    // Clear invalid file from the input.
    fileInput.value = ''

    const allowedLabel = getAllowedLabel(allowedTypes)

    showError(
      fileInput,
      `Unsupported file type. Allowed: ${allowedLabel}.`,
    )

    return false
  }

  fileInputs.forEach((fileInput) => {
    /**
     * Validate standard file picker uploads.
     */
    fileInput.addEventListener('change', (event) => {
      removeErrors()

      const file = event.target.files?.[0]

      if (!file) return

      validateFile(fileInput, file)
    })

    /**
     * Validate drag & drop uploads.
     *
     * Prevents unsupported files from being attached to the input.
     */
    fileInput.addEventListener('drop', (event) => {
      const file = event.dataTransfer?.files?.[0]

      if (!file) return

      const allowedTypes = getAllowedTypes(fileInput)

      if (allowedTypes.length && !isValidFile(file, allowedTypes)) {
        event.preventDefault()
        event.stopPropagation()

        removeErrors()

        const allowedLabel = getAllowedLabel(allowedTypes)

        showError(
          fileInput,
          `Unsupported file type. Allowed: ${allowedLabel}.`,
        )
      }
    })
  })

  /**
   * Prevent the browser from opening dropped files outside the file input.
   */
  document.addEventListener('dragover', (event) => {
    event.preventDefault()
  })
})
