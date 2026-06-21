import { createContext, useContext, useState, useCallback } from 'react'
import { login as apiLogin, signup as apiSignup } from '../lib/api'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [user, setUser]               = useState(() => {
    try { return JSON.parse(localStorage.getItem('jtickets_user') || 'null') }
    catch { return null }
  })
  const [events, setEvents]           = useState([])
  const [eventsLoading, setEventsLoading] = useState(true)
  const [authOpen, setAuthOpen]       = useState(false)
  const [bookingEvent, setBookingEvent] = useState(null)
  const [toasts, setToasts]           = useState([])
  const [category, setCategory]       = useState('all')

  const addToast = useCallback((message, type = 'success') => {
    const id = Date.now()
    setToasts((t) => [...t, { id, message, type }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000)
  }, [])

  const doLogin = useCallback(async (email, password) => {
    const res = await apiLogin(email, password)
    const token = res.data.access_token
    localStorage.setItem('jtickets_token', token)
    // Decode role from JWT payload (base64url)
    const [, payloadB64] = token.split('.')
    const payload = JSON.parse(atob(payloadB64.replace(/-/g, '+').replace(/_/g, '/')))
    const u = { email, role: payload.role, id: payload.sub }
    localStorage.setItem('jtickets_user', JSON.stringify(u))
    setUser(u)
    return u
  }, [])

  const doSignup = useCallback(async (email, password, role) => {
    await apiSignup({ email, password, role })
    return doLogin(email, password)
  }, [doLogin])

  const logout = useCallback(() => {
    localStorage.removeItem('jtickets_token')
    localStorage.removeItem('jtickets_user')
    setUser(null)
    addToast('Logged out. See you soon! 👋')
  }, [addToast])

  const openBooking = useCallback((event) => {
    if (!user) { setAuthOpen(true); return }
    if (user.role !== 'customer') { addToast('Only customers can book tickets.', 'error'); return }
    setBookingEvent(event)
  }, [user, addToast])

  return (
    <AppContext.Provider value={{
      user, events, setEvents, eventsLoading, setEventsLoading,
      authOpen, setAuthOpen,
      bookingEvent, setBookingEvent,
      toasts, addToast,
      category, setCategory,
      doLogin, doSignup, logout, openBooking,
    }}>
      {children}
    </AppContext.Provider>
  )
}

export const useApp = () => useContext(AppContext)
