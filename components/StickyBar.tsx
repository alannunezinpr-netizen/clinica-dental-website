export default function StickyBar() {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white shadow-2xl border-t border-gray-200 p-4 md:hidden z-40">
      <div className="flex gap-3 max-w-lg mx-auto">
        <a
          href="tel:7877379150"
          className="flex-1 bg-primary-500 hover:bg-primary-600 text-white font-bold py-4 px-6 rounded-full transition-all duration-300 shadow-lg active:scale-95 flex items-center justify-center gap-2 focus:outline-none focus:ring-4 focus:ring-primary-300"
          style={{ minHeight: '56px' }}
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
          </svg>
          <span>Llamar</span>
        </a>

        <a
          href="https://www.google.com/maps/search/?api=1&query=Plaza+Nazario+Calle+A.+Aruz+Rivera+200E+Suite+B4+Gurabo+Puerto+Rico+00778"
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 bg-white hover:bg-gray-50 text-primary-600 font-bold py-4 px-6 rounded-full transition-all duration-300 shadow-lg border-2 border-primary-200 active:scale-95 flex items-center justify-center gap-2 focus:outline-none focus:ring-4 focus:ring-primary-300"
          style={{ minHeight: '56px' }}
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span>Cómo llegar</span>
        </a>
      </div>
    </div>
  )
}
