import { useEffect, useState } from 'react'
import { AppProvider, useApp, PAGES } from './context/AppContext'
import { getEvents } from './lib/api'
import Navbar              from './components/Navbar'
import Hero                from './components/Hero'
import Categories          from './components/Categories'
import EventsSection       from './components/EventsSection'
import Footer              from './components/Footer'
import AuthModal           from './components/AuthModal'
import BookingModal        from './components/BookingModal'
import Toast               from './components/Toast'
import EventDetail         from './components/EventDetail'
import OrganizerDashboard  from './components/OrganizerDashboard'
import SupportWidget       from './components/SupportWidget'
import styles              from './App.module.css'

function LegalPage({ type }) {
  const [content, setContent] = useState('')
  useEffect(() => {
    const fn = type === 'terms'
      ? () => import('./lib/api').then(m => m.getTerms())
      : () => import('./lib/api').then(m => m.getPrivacy())
    fn().then(r => setContent(r.data.content)).catch(() => {})
  }, [type])
  return (
    <div className={styles.legalPage}>
      <pre className={styles.legalContent}>{content}</pre>
    </div>
  )
}

function AppInner() {
  const {
    authOpen, bookingEvent, setEvents, setEventsLoading,
    page, goHome, user, PAGES,
  } = useApp()
  const [supportOpen, setSupportOpen] = useState(false)

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
        {page === PAGES.HOME && (
          <>
            <Hero onExplore={scrollToEvents} />
            <Categories />
            <EventsSection />
          </>
        )}
        {page === PAGES.EVENT      && <EventDetail />}
        {page === PAGES.ORGANIZER  && <OrganizerDashboard />}
        {page === PAGES.TERMS      && <LegalPage type="terms" />}
        {page === PAGES.PRIVACY    && <LegalPage type="privacy" />}
      </main>

      <Footer onSupport={() => setSupportOpen(true)} />

      {authOpen      && <AuthModal />}
      {bookingEvent  && <BookingModal />}
      <Toast />

      {/* Floating support button */}
      <button
        className={styles.supportFab}
        onClick={() => setSupportOpen(s => !s)}
        title="Chat with Support"
      >
        {supportOpen ? '✕' : '💬'}
      </button>

      {supportOpen && <SupportWidget onClose={() => setSupportOpen(false)} />}
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
