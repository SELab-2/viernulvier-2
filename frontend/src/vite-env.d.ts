/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly PUBLIC_API_KEY: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare global {
  interface Window {
    __vnv_root__?: import('react-dom/client').Root
  }
}
