import { useEffect, useRef } from 'react'
import { AppProvider, useApp } from './context/AppContext'
import { getEvents } from './lib/api'
import Navbar        from './components/Navbar'
import Hero          from './components/Hero'
import Categories    from './components/Categories'
import EventsSection from './components/EventsSection'
import HowItWorks    from './components/HowItWorks'
import Footer        from './components/Footer'
import AuthModal     from './components/AuthModal'
import BookingModal  from './components/BookingModal'
import Toast         from './components/Toast'

function AppInner() {
  const { authOpen, bookingEvent, setEvents, setEventsLoading } = useApp()
  const eventsRef = useRef(null)

  useEffect(() => {
    getEvents()
      .then((r) => setEvents(r.data))
      .catch(console.error)
      .finally(() => setEventsLoading(false))
  }, [])

  function scrollToEvents() {
    document.getElementById('events')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <>
      <Navbar onExplore={scrollToEvents} />
      <main>
        <Hero onExplore={scrollToEvents} />
        <Categories />
        <EventsSection />
        <HowItWorks />
      </main>
      <Footer />

      {authOpen    && <AuthModal />}
      {bookingEvent && <BookingModal />}
      <Toast />
    </>
  )
}

export default function App() {
  return (
    <AppProvider>
      <AppInner />
    </AppProvider>
  )
}
