import { useEffect, useRef, useState, useCallback } from 'react'
import { useApp } from '../context/AppContext'
import { getNotifications, markNotificationRead, markAllNotificationsRead } from '../lib/api'
import styles from './NotificationBell.module.css'

const POLL_MS = 15000

function timeAgo(iso) {
  const s = Math.max(1, Math.floor((Date.now() - new Date(iso).getTime()) / 1000))
  if (s < 60) return `${s}s ago`
  const m = Math.floor(s / 60); if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60); if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

const ICON = { event_updated: '🔔', booking_confirmed: '🎟️' }

export default function NotificationBell() {
  const { user } = useApp()
  const [items, setItems] = useState([])
  const [open, setOpen] = useState(false)
  const wrapRef = useRef(null)

  const load = useCallback(async () => {
    try {
      const { data } = await getNotifications()
      setItems(data)
    } catch { /* not logged in / transient — ignore */ }
  }, [])

  // Poll while logged in.
  useEffect(() => {
    if (!user) { setItems([]); return }
    load()
    const t = setInterval(load, POLL_MS)
    return () => clearInterval(t)
  }, [user, load])

  // Close on outside click.
  useEffect(() => {
    if (!open) return
    const onClick = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [open])

  if (!user) return null

  const unread = items.filter((n) => !n.is_read).length

  const openOne = async (n) => {
    if (n.is_read) return
    setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)))
    try { await markNotificationRead(n.id) } catch { load() }
  }

  const clearAll = async () => {
    setItems((prev) => prev.map((x) => ({ ...x, is_read: true })))
    try { await markAllNotificationsRead() } catch { load() }
  }

  return (
    <div className={styles.wrap} ref={wrapRef}>
      <button
        className={styles.bell}
        aria-label={`Notifications${unread ? ` (${unread} unread)` : ''}`}
        onClick={() => setOpen((o) => !o)}
      >
        🔔
        {unread > 0 && <span className={styles.badge}>{unread > 9 ? '9+' : unread}</span>}
      </button>

      {open && (
        <div className={styles.panel}>
          <div className={styles.head}>
            <span>Notifications</span>
            {unread > 0 && (
              <button className={styles.markAll} onClick={clearAll}>Mark all read</button>
            )}
          </div>

          {items.length === 0 ? (
            <div className={styles.empty}>You're all caught up ✨</div>
          ) : (
            <ul className={styles.list}>
              {items.map((n) => (
                <li
                  key={n.id}
                  className={`${styles.item} ${n.is_read ? '' : styles.unreadItem}`}
                  onClick={() => openOne(n)}
                >
                  <span className={styles.icon}>{ICON[n.type] || '🔔'}</span>
                  <div className={styles.body}>
                    <p className={styles.msg}>{n.message}</p>
                    <span className={styles.time}>{timeAgo(n.created_at)}</span>
                  </div>
                  {!n.is_read && <span className={styles.dot} />}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
