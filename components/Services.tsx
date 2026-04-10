const ServiceCard = ({ title, icon, items }: { title: string; icon: React.ReactNode; items: string[] }) => (
  <div className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow duration-300 border border-gray-100">
    <div className="flex items-center gap-4 mb-6">
      <div className="w-14 h-14 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
        {icon}
      </div>
      <h3 className="text-2xl font-bold text-gray-900">{title}</h3>
    </div>
    <ul className="space-y-3">
      {items.map((item, idx) => (
        <li key={idx} className="flex items-start gap-3">
          <svg className="w-6 h-6 text-primary-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span className="text-gray-700">{item}</span>
        </li>
      ))}
    </ul>
  </div>
)

export default function Services() {
  return (
    <section id="servicios" className="py-20 bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">Nuestros Servicios</h2>
          <div className="w-20 h-1 bg-primary-400 mx-auto rounded-full mb-6" />
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Ofrecemos atención dental completa para niños y adultos
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <ServiceCard
            title="Atención Pediátrica"
            icon={
              <svg className="w-7 h-7 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            items={[
              'Dentista pediátrico especializado',
              'Atención dental especializada para niños',
              'Prevención y cuidado oral infantil',
            ]}
          />

          <ServiceCard
            title="Odontología General"
            icon={
              <svg className="w-7 h-7 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            }
            items={[
              'Odontología general para toda la familia',
              'Limpiezas dentales profesionales',
              'Exámenes dentales completos',
            ]}
          />
        </div>
      </div>
    </section>
  )
}
