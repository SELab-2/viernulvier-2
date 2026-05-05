import type { ReactNode } from 'react'

type DocumentProps = {
  children?: ReactNode
}

export const Document = ({ children }: DocumentProps) => children ?? null

export const Page = () => null

export const pdfjs = {
  GlobalWorkerOptions: {
    workerSrc: '',
  },
  version: '5.4.296',
}
