export default function Contact() {
  return (
    <section id="contacto" className="py-20 bg-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">Contacto</h2>
          <div className="w-20 h-1 bg-primary-400 mx-auto rounded-full" />
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <div className="bg-gradient-to-br from-primary-50 to-cyan-50 rounded-2xl p-8 shadow-lg">
            <div className="flex items-start gap-4 mb-6">
              <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center flex-shrink-0 shadow-sm">
                <svg className="w-6 h-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Teléfono</h3>
                <a
                  href="tel:7877379150"
                  className="text-2xl font-bold text-primary-600 hover:text-primary-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
                >
                  787-737-9150
                </a>
              </div>
            </div>
            <p className="text-gray-600 text-sm">
              Llámanos para programar una cita o resolver cualquier duda
            </p>
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 shadow-lg">
            <div className="flex items-start gap-4 mb-6">
              <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center flex-shrink-0 shadow-sm">
                <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">Facebook</h3>
                <a
                  href="https://www.facebook.com/people/Clinica-Dental-Dentista-Pediatrico-Dra-Maria-Berrios-Hernandez/100063558208355/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-700 font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded inline-block"
                >
                  Visita nuestra página →
                </a>
              </div>
            </div>
            <p className="text-gray-600 text-sm">
              Síguenos en Facebook para actualizaciones y consejos de salud dental
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
