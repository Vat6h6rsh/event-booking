import axios from 'axios'

const api = axios.create({
  // In dev: Vite proxy rewrites /api → http://127.0.0.1:8000
  // In prod: set VITE_API_URL to https://your-render-app.onrender.com
  baseURL: import.meta.env.VITE_API_URL || '/api',
})

// Attach token from localStorage to every request if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('jtickets_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const signup = (data) => api.post('/signup', data)
export const login  = (email, password) =>
  api.post('/login', new URLSearchParams({ username: email, password }), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })

export const getEvents  = (skip = 0, limit = 100) => api.get(`/events?skip=${skip}&limit=${limit}`)
export const getEvent   = (id) => api.get(`/events/${id}`)
export const createBook = (eventId, quantity) => api.post('/bookings', { event_id: eventId, quantity })
export const myBookings = () => api.get('/bookings')

export default api
