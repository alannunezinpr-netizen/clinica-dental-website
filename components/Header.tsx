'use client'

import { useState } from 'react'

const Logo = ({ variant = 'full' }: { variant?: 'full' | 'icon' }) => (
  <div className="flex items-center gap-3">
    <svg width="48" height="48" viewBox="0 0 48 48" fill="none" className="flex-shrink-0">
      <path d="M24 4C18.5 4 14 8.5 14 14C14 16.5 14.9 18.8 16.4 20.6L24 38L31.6 20.6C33.1 18.8 34 16.5 34 14C34 8.5 29.5 4 24 4Z" fill="#38bdf8"/>
      <ellipse cx="24" cy="14" rx="6" ry="7" fill="white"/>
      <path d="M21 13C21 13 22 11.5 24 11.5C26 11.5 27 13 27 13" stroke="#38bdf8" strokeWidth="1.5" strokeLinecap="round"/>
      <circle cx="21.5" cy="12" r="1" fill="#38bdf8"/>
      <circle cx="26.5" cy="12" r="1" fill="#38bdf8"/>
      <path d="M20 17L22 19L26 15" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity="0.6"/>
    </svg>
    {variant === 'full' && (
      <div className="flex flex-col">
        <span className="font-bold text-gray-800 text-sm md:text-base leading-tight">
          Clínica Dental & Dentista Pediátrico
        </span>
        <span className="text-xs text-gray-600">Dra. María Berríos Hernández</span>
      </div>
    )}
  </div>
)

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const navItems = [
    { label: 'Inicio', href: '#inicio' },
    { label: 'Nuestra Clínica', href: '#about' },
    { label: 'Servicios', href: '#servicios' },
    { label: 'Horario', href: '#horario' },
    { label: 'Ubicación', href: '#ubicacion' },
    { label: 'Contacto', href: '#contacto' },
  ]

  return (
    <header className="bg-white shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          <a href="#inicio" className="focus:outline-none focus:ring-2 focus:ring-primary-500 rounded-lg">
            <Logo variant="full" />
          </a>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-8">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="text-gray-700 hover:text-primary-600 font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded px-2 py-1"
              >
                {item.label}
              </a>
            ))}
          </nav>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
            aria-label="Menú"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && (
          <nav className="lg:hidden pb-4 border-t border-gray-100 mt-2">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                onClick={() => setIsMenuOpen(false)}
                className="block py-3 text-gray-700 hover:text-primary-600 hover:bg-gray-50 font-medium transition-colors duration-200 px-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {item.label}
              </a>
            ))}
          </nav>
        )}
      </div>
    </header>
  )
}
