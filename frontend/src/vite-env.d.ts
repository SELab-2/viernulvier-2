/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly PUBLIC_API_KEY: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
