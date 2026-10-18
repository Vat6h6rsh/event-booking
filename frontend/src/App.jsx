import { useEffect, useState } from 'react'
import { AppProvider, useApp, PAGES } from './context/AppContext'
import { errorDetail } from './lib/booking'
import MyBookings from './components/MyBookings'
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
    page, goHome, user, PAGES, setEventsError, catalogueVersion,
  } = useApp()
  const [supportOpen, setSupportOpen] = useState(false)

  useEffect(() => {
    let ignore = false
    setEventsLoading(true); setEventsError('')
    async function load() {
      const all = []
      for (let offset = 0; ; offset += 100) {
        const { data } = await getEvents({ limit: 100, skip: offset })
        if (ignore) return
        all.push(...data)
        if (data.length < 100) break
      }
      if (!ignore) setEvents(all)
    }
    load().catch(ex => { if (!ignore) setEventsError(errorDetail(ex, 'Could not refresh events. Retry to load the catalogue.')) })
      .finally(() => { if (!ignore) setEventsLoading(false) })
    return () => { ignore = true }
  }, [catalogueVersion])
  useEffect(() => {
    document.title = `${({ home: 'Discover events', bookings: 'My tickets', event: 'Event details', organizer: 'Organizer dashboard', terms: 'Terms', privacy: 'Privacy', venue: 'Venue', support: 'Support' })[page] || 'JTickets'} | JTickets`
    document.getElementById('main-content')?.focus({ preventScroll: true })
  }, [page])

  function scrollToEvents() {
    document.getElementById('events')?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
  }

  return (
    <>
      <Navbar onExplore={scrollToEvents} />

      <a className="skip-link" href="#main-content">Skip to content</a>
      <main id="main-content" tabIndex={-1}>
        {page === PAGES.HOME && (
          <>
            <Hero onExplore={scrollToEvents} />
            <Categories />
            <EventsSection />
          </>
        )}
        {page === PAGES.BOOKINGS && <MyBookings />}
        {page === PAGES.EVENT      && <EventDetail />}
        {page === PAGES.ORGANIZER  && <OrganizerDashboard />}
        {page === PAGES.TERMS      && <LegalPage type="terms" />}
        {page === PAGES.PRIVACY    && <LegalPage type="privacy" />}
      </main>

      <div className={page === PAGES.EVENT ? styles.eventFooter : undefined}><Footer onSupport={() => setSupportOpen(true)} /></div>

      {authOpen      && <AuthModal />}
      {bookingEvent  && <BookingModal key={bookingEvent.id} />}
      <Toast />

      {/* Floating support button */}
      {!bookingEvent && page !== PAGES.EVENT && <button
        className={styles.supportFab}
        onClick={() => setSupportOpen(s => !s)}
        title="Chat with Support"
      >
        {supportOpen ? '✕' : '💬'}
      </button>}

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
