import { createContext, useContext, useState, useCallback } from 'react'
import { login as apiLogin, signup as apiSignup } from '../lib/api'

const AppContext = createContext(null)

export const PAGES = {
  HOME: 'home', EVENT: 'event',
  ORGANIZER: 'organizer', VENUE: 'venue',
  BOOKINGS: 'bookings', SUPPORT: 'support',
  TERMS: 'terms', PRIVACY: 'privacy',
}

export function AppProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('jtickets_user') || 'null') }
    catch { return null }
  })
  const [events, setEvents]               = useState([])
  const [eventsLoading, setEventsLoading] = useState(true)
  const [authOpen, setAuthOpen]           = useState(false)
  const [bookingEvent, setBookingEvent]   = useState(null)
  const [toasts, setToasts]               = useState([])
  const [category, setCategory]           = useState('all')
  const [page, setPage]                   = useState(PAGES.HOME)
  const [selectedEvent, setSelectedEvent] = useState(null)  // for EventDetail

  const addToast = useCallback((message, type = 'success') => {
    const id = Date.now()
    setToasts((t) => [...t, { id, message, type }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4500)
  }, [])

  const doLogin = useCallback(async (email, password) => {
    const res  = await apiLogin(email, password)
    const { access_token, user: u } = res.data
    localStorage.setItem('jtickets_token', access_token)
    localStorage.setItem('jtickets_user', JSON.stringify(u))
    setUser(u)
    return u
  }, [])

  const doSignup = useCallback(async (email, password, role, full_name) => {
    await apiSignup({ email, password, role, full_name })
    return doLogin(email, password)
  }, [doLogin])

  const logout = useCallback(() => {
    localStorage.removeItem('jtickets_token')
    localStorage.removeItem('jtickets_user')
    setUser(null)
    setPage(PAGES.HOME)
    addToast('Logged out. See you soon!')
  }, [addToast])

  const openBooking = useCallback((event) => {
    if (!user) { setAuthOpen(true); return }
    if (user.role !== 'customer') { addToast('Only customers can book tickets.', 'error'); return }
    setBookingEvent(event)
  }, [user, addToast])

  const goToEvent = useCallback((event) => {
    setSelectedEvent(event)
    setPage(PAGES.EVENT)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  const goHome = useCallback(() => {
    setPage(PAGES.HOME)
    setSelectedEvent(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  return (
    <AppContext.Provider value={{
      user, events, setEvents, eventsLoading, setEventsLoading,
      authOpen, setAuthOpen,
      bookingEvent, setBookingEvent,
      toasts, addToast,
      category, setCategory,
      page, setPage, PAGES,
      selectedEvent, setSelectedEvent,
      doLogin, doSignup, logout,
      openBooking, goToEvent, goHome,
    }}>
      {children}
    </AppContext.Provider>
  )
}

export const useApp = () => useContext(AppContext)
