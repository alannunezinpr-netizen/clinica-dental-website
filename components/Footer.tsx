export default function Footer() {
  return (
    <footer className="bg-gray-900 text-white py-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid md:grid-cols-3 gap-8 mb-8">
          <div>
            <h3 className="text-xl font-bold mb-4">Clínica Dental & Dentista Pediátrico</h3>
            <p className="text-gray-400">Dra. María Berríos Hernández</p>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Ubicación</h4>
            <p className="text-gray-400 text-sm leading-relaxed">
              Plaza Nazario<br />
              Calle A. Aruz Rivera #200E, Suite B4<br />
              Gurabo, Puerto Rico 00778
            </p>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Contacto</h4>
            <p className="text-gray-400 text-sm">
              <a href="tel:7877379150" className="hover:text-primary-300 transition-colors duration-200">
                787-737-9150
              </a>
            </p>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-8 text-center text-gray-500 text-sm">
          <p>&copy; {new Date().getFullYear()} Clínica Dental & Dentista Pediátrico – Dra. María Berríos Hernández. Todos los derechos reservados.</p>
        </div>
      </div>
    </footer>
  )
}
