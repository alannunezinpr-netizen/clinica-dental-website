export default function Schedule() {
  const schedule = [
    { day: 'Lunes', hours: 'Cerrado', closed: true },
    { day: 'Martes', hours: '9:00 a.m. – 3:30 p.m.', closed: false },
    { day: 'Miércoles', hours: '9:00 a.m. – 3:30 p.m.', closed: false },
    { day: 'Jueves', hours: '9:00 a.m. – 3:30 p.m.', closed: false },
    { day: 'Viernes', hours: 'Cerrado', closed: true },
    { day: 'Sábado', hours: '9:00 a.m. – 12:30 p.m.', closed: false },
    { day: 'Domingo', hours: 'Cerrado', closed: true },
  ]

  return (
    <section id="horario" className="py-20 bg-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">Horario de Atención</h2>
          <div className="w-20 h-1 bg-primary-400 mx-auto rounded-full" />
        </div>

        <div className="bg-gradient-to-br from-primary-50 to-cyan-50 rounded-3xl p-8 md:p-12 shadow-lg">
          <div className="space-y-4">
            {schedule.map((item, idx) => (
              <div
                key={idx}
                className={`flex justify-between items-center p-4 rounded-xl transition-all duration-200 ${
                  item.closed
                    ? 'bg-white/50 text-gray-500'
                    : 'bg-white shadow-sm hover:shadow-md'
                }`}
              >
                <span className="font-semibold text-lg">{item.day}</span>
                <span className={`font-medium ${item.closed ? 'text-gray-400' : 'text-primary-700'}`}>
                  {item.hours}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
