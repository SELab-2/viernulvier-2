document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.querySelector('input[type="file"][name="file"]')
  if (!fileInput) return

  const ALLOWED_TYPES = [
    'image/jpeg',
    'image/png',
    'image/webp',
    'application/pdf',
  ]

  const isValidFile = (file) => ALLOWED_TYPES.includes(file.type)

  const removeErrors = () => {
    document.querySelectorAll('.errorlist').forEach(el => el.remove())
    document.querySelectorAll('.errornote').forEach(el => el.remove())
    document.querySelectorAll('.errors').forEach(el => el.classList.remove('errors'))
  }

  const showError = (message) => {
    // 🔴 1. field-level error
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

    // 🔴 2. global error banner
    const form = fileInput.closest('form')
    if (form && !form.querySelector('.errornote')) {
      const p = document.createElement('p')
      p.className = 'errornote'
      p.textContent = 'Please correct the error below.'

      form.prepend(p)
    }
  }

  const validateFile = (file) => {
    if (!isValidFile(file)) {
      fileInput.value = ''
      showError('Unsupported file type. Allowed: JPG, PNG, WEBP, PDF.')
      return false
    }
    return true
  }

  // =========================
  // normale selectie
  // =========================
  fileInput.addEventListener('change', (e) => {
    removeErrors()

    const file = e.target.files?.[0]
    if (!file) return

    validateFile(file)
  })

  // =========================
  // drag & drop (global)
  // =========================
  document.addEventListener('drop', (e) => {
    const file = e.dataTransfer?.files?.[0]
    if (!file) return

    if (!isValidFile(file)) {
      e.preventDefault()
      e.stopPropagation()

      removeErrors()
      showError('Unsupported file type. Allowed: JPG, PNG, WEBP, PDF.')
    }
  })

  document.addEventListener('dragover', (e) => {
    e.preventDefault()
  })
})
