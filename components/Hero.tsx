'use client'

import { useEffect, useState } from 'react'

const ToothIcon = () => (
  <svg width="120" height="120" viewBox="0 0 120 120" fill="none" className="mx-auto mb-6">
    <path d="M60 10C42.5 10 28 24.5 28 42C28 50 30.8 57.3 35.6 63L60 110L84.4 63C89.2 57.3 92 50 92 42C92 24.5 77.5 10 60 10Z" fill="white" fillOpacity="0.95"/>
    <ellipse cx="60" cy="42" rx="18" ry="22" fill="white"/>
    <path d="M48 40C48 40 52 35 60 35C68 35 72 40 72 40" stroke="#7dd3fc" strokeWidth="3" strokeLinecap="round"/>
    <circle cx="52" cy="38" r="2.5" fill="#7dd3fc"/>
    <circle cx="68" cy="38" r="2.5" fill="#7dd3fc"/>
    <path d="M45 52L52 59L68 43" stroke="#7dd3fc" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" opacity="0.5"/>
  </svg>
)

const ClockIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="10"/>
    <polyline points="12 6 12 12 16 14"/>
  </svg>
)

const PinIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
    <circle cx="12" cy="10" r="3"/>
  </svg>
)

function getTodayStatus(): string {
  const days = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
  const today = new Date().getDay()
  const dayName = days[today]

  const schedule: { [key: string]: string } = {
    'Lunes': 'Cerrado',
    'Martes': '9:00 a.m. – 3:30 p.m.',
    'Miércoles': '9:00 a.m. – 3:30 p.m.',
    'Jueves': '9:00 a.m. – 3:30 p.m.',
    'Viernes': 'Cerrado',
    'Sábado': '9:00 a.m. – 12:30 p.m.',
    'Domingo': 'Cerrado',
  }

  return schedule[dayName] || 'Cerrado'
}

export default function Hero() {
  const [todayStatus, setTodayStatus] = useState('')

  useEffect(() => {
    setTodayStatus(getTodayStatus())
  }, [])

  return (
    <section id="inicio" className="relative min-h-[80vh] flex items-center justify-center overflow-hidden bg-gradient-to-br from-primary-300 via-primary-200 to-cyan-200">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-[0.15]" style={{ backgroundImage: 'var(--bg-pattern)' }} />
      
      {/* Organic Shapes */}
      <div className="absolute top-0 left-0 w-96 h-96 bg-white/10 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2" />
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-cyan-300/20 rounded-full blur-3xl translate-x-1/3 translate-y-1/3" />

      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <ToothIcon />
        
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-4 leading-tight">
          Clínica Dental & Dentista Pediátrico
        </h1>
        
        <p className="text-xl sm:text-2xl text-white/95 mb-12 max-w-3xl mx-auto">
          Odontología general y cuidado dental especializado para niños
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
          <a
            href="tel:7877379150"
            className="btn-primary inline-flex items-center gap-3 w-full sm:w-auto justify-center"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
            </svg>
            <span>Llamar ahora</span>
          </a>
          
          <a
            href="https://www.google.com/maps/search/?api=1&query=Plaza+Nazario+Calle+A.+Aruz+Rivera+200E+Suite+B4+Gurabo+Puerto+Rico+00778"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary inline-flex items-center gap-3 w-full sm:w-auto justify-center"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
              <circle cx="12" cy="10" r="3"/>
            </svg>
            <span>Cómo llegar</span>
          </a>
        </div>

        {/* Glass Cards */}
        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          <div className="glass-card rounded-2xl p-6 text-left">
            <div className="flex items-center gap-3 text-white/80 mb-2">
              <ClockIcon />
              <span className="text-sm font-medium uppercase tracking-wide">Hoy</span>
            </div>
            <p className="text-2xl font-bold text-white">
              {todayStatus || 'Cargando...'}
            </p>
          </div>

          <div className="glass-card rounded-2xl p-6 text-left">
            <div className="flex items-center gap-3 text-white/80 mb-2">
              <PinIcon />
              <span className="text-sm font-medium uppercase tracking-wide">Gurabo, PR</span>
            </div>
            <p className="text-lg font-semibold text-white leading-snug">
              Plaza Nazario, Calle A. Aruz Rivera #200E, Suite B4
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
