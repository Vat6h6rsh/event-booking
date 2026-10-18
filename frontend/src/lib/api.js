import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 60000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('jtickets_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auth
export const signup  = (d) => api.post('/signup', d)
export const login   = (email, password) =>
  api.post('/login', new URLSearchParams({ username: email, password }), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })

// Users
export const getMe      = ()    => api.get('/users/me')
export const updateMe   = (d)   => api.put('/users/me', d)

// Events
export const getEvents  = (params = {}) => api.get('/events', { params })
export const getEvent   = (id)  => api.get(`/events/${id}`)
export const getMyEvents= ()    => api.get('/events/mine')
export const getMyEventStats = () => api.get('/events/mine/stats')
export const createEvent= (d)   => api.post('/events', d)
export const updateEvent= (id,d)=> api.put(`/events/${id}`, d)
export const deleteEvent= (id)  => api.delete(`/events/${id}`)

// Tiers
export const getTiers   = (eid) => api.get(`/events/${eid}/tiers`)
export const createTier = (eid,d)=> api.post(`/events/${eid}/tiers`, d)
export const updateTier = (eid,tid,d)=> api.put(`/events/${eid}/tiers/${tid}`, d)
export const deleteTier = (eid,tid)  => api.delete(`/events/${eid}/tiers/${tid}`)

// Seats
export const getSeatAvailability = (eid) => api.get(`/events/${eid}/seats`)

// Bookings
export const createBooking = (d, key) => api.post('/bookings', d, { headers: { 'Idempotency-Key': key } })
export const myBookings    = ()   => api.get('/bookings')
export const getBooking    = (id) => api.get(`/bookings/${id}`)
export const cancelBooking = (id) => api.delete(`/bookings/${id}`)

// Venues
export const getVenues    = (params = {}) => api.get('/venues', { params })
export const getMyVenues  = ()    => api.get('/venues/mine')
export const createVenue  = (d)   => api.post('/venues', d)
export const updateVenue  = (id,d)=> api.put(`/venues/${id}`, d)

// Support
export const createSupportTicket = (d)     => api.post('/support/tickets', d)
export const mySupportTickets    = ()      => api.get('/support/tickets')
export const getSupportTicket    = (id)    => api.get(`/support/tickets/${id}`)
export const updateSupportTicket = (id, d) => api.put(`/support/tickets/${id}`, d)
export const getSupportMessages  = (id)    => api.get(`/support/tickets/${id}/messages`)
export const sendSupportMessage  = (id, m) => api.post(`/support/tickets/${id}/messages`, { message: m })

// Upload
export const uploadImage = (file) => {
  const fd = new FormData(); fd.append('file', file)
  return api.post('/upload/image', fd)
}

// Notifications (written by the background tasks — Task 2 shows up here in-app)
export const getNotifications      = ()   => api.get('/notifications')
export const markNotificationRead  = (id) => api.post(`/notifications/${id}/read`)
export const markAllNotificationsRead = () => api.post('/notifications/read-all')

// Legal
export const getTerms   = () => api.get('/legal/terms')
export const getPrivacy = () => api.get('/legal/privacy')

export default api
