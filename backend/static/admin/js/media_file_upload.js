document.addEventListener('DOMContentLoaded', () => {
  const fileInputs = document.querySelectorAll('input[type="file"]')

  if (!fileInputs.length) return

  const MIME_TYPE_BY_EXTENSION = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.webp': 'image/webp',
    '.pdf': 'application/pdf',
  }

  const getAllowedTypes = (fileInput) => {
    const accept = fileInput.getAttribute('accept') || ''

    return accept
      .split(',')
      .map((value) => value.trim().toLowerCase())
      .filter(Boolean)
      .map((value) => MIME_TYPE_BY_EXTENSION[value] || value)
  }

  const getAllowedLabel = (allowedTypes) => {
    const labels = []

    if (allowedTypes.includes('image/jpeg')) labels.push('JPG')
    if (allowedTypes.includes('image/png')) labels.push('PNG')
    if (allowedTypes.includes('image/webp')) labels.push('WEBP')
    if (allowedTypes.includes('application/pdf')) labels.push('PDF')

    return labels.join(', ')
  }

  const removeErrors = () => {
    document.querySelectorAll('.errorlist').forEach((el) => el.remove())
    document.querySelectorAll('.errornote').forEach((el) => el.remove())
    document.querySelectorAll('.errors').forEach((el) => el.classList.remove('errors'))
  }

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

    const form = fileInput.closest('form')
    if (form && !form.querySelector('.errornote')) {
      const p = document.createElement('p')
      p.className = 'errornote'
      p.textContent = 'Please correct the error below.'
      form.prepend(p)
    }
  }

  const isValidFile = (file, allowedTypes) => allowedTypes.includes(file.type)

  const validateFile = (fileInput, file) => {
    const allowedTypes = getAllowedTypes(fileInput)

    if (!allowedTypes.length || isValidFile(file, allowedTypes)) {
      return true
    }

    fileInput.value = ''

    const allowedLabel = getAllowedLabel(allowedTypes)
    showError(fileInput, `Unsupported file type. Allowed: ${allowedLabel}.`)

    return false
  }

  fileInputs.forEach((fileInput) => {
    fileInput.addEventListener('change', (event) => {
      removeErrors()

      const file = event.target.files?.[0]
      if (!file) return

      validateFile(fileInput, file)
    })

    fileInput.addEventListener('drop', (event) => {
      const file = event.dataTransfer?.files?.[0]
      if (!file) return

      const allowedTypes = getAllowedTypes(fileInput)

      if (allowedTypes.length && !isValidFile(file, allowedTypes)) {
        event.preventDefault()
        event.stopPropagation()

        removeErrors()

        const allowedLabel = getAllowedLabel(allowedTypes)
        showError(fileInput, `Unsupported file type. Allowed: ${allowedLabel}.`)
      }
    })
  })

  document.addEventListener('dragover', (event) => {
    event.preventDefault()
  })
})
