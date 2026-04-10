import Header from '@/components/Header'
import Hero from '@/components/Hero'
import About from '@/components/About'
import Services from '@/components/Services'
import Schedule from '@/components/Schedule'
import Location from '@/components/Location'
import Contact from '@/components/Contact'
import Footer from '@/components/Footer'
import StickyBar from '@/components/StickyBar'

export default function Home() {
  return (
    <>
      <Header />
      <main>
        <Hero />
        <About />
        <Services />
        <Schedule />
        <Location />
        <Contact />
      </main>
      <Footer />
      <StickyBar />
    </>
  )
}
