import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Clínica Dental & Dentista Pediátrico – Dra. María Berríos Hernández',
  description: 'Odontología general y cuidado dental especializado para niños en Gurabo, Puerto Rico',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  )
}
