import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Monad — Portable Cognitive AI',
  description: 'A portable, local-first AI cognitive architecture with 82 organs, self-improvement, and multi-model fusion.',
  icons: {
    icon: 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22%3E%3Ctext y=%22.9em%22 font-size=%2290%22%3E🧠%3C/text%3E%3C/svg%3E',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-monad-radial">{children}</body>
    </html>
  )
}
