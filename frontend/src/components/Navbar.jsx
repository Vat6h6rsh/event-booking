import { useEffect, useRef, useState } from 'react'
import { useApp, PAGES } from '../context/AppContext'
import NotificationBell from './NotificationBell'
import styles from './Navbar.module.css'

export default function Navbar({ onExplore }) {
  const { user, logout, setAuthOpen, setAuthTab, page, setPage, goHome } = useApp()
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const navRef = useRef(null)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  function nav(pg) { setPage(pg); setMenuOpen(false); window.scrollTo({ top:0, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }) }

  return (
    <nav ref={navRef} className={`${styles.nav} ${scrolled ? styles.scrolled : ''}`}>
      <div className={styles.inner}>
        {/* Logo */}
        <button className={styles.logo} onClick={goHome}>
          <span className={styles.logoIcon}>🎟️</span>
          <span className={styles.logoText}>Jtickets</span>
        </button>

        {/* Desktop nav links */}
        <ul className={styles.links}>
          <li><button onClick={() => { goHome(); setTimeout(onExplore, 100) }}>Events</button></li>
          {user?.role === 'organizer' && (
            <li><button className={page === PAGES.ORGANIZER ? styles.linkActive : ''} onClick={() => nav(PAGES.ORGANIZER)}>Dashboard</button></li>
          )}
          {user?.role === 'customer' && <li><button aria-current={page === PAGES.BOOKINGS ? 'page' : undefined} onClick={() => nav(PAGES.BOOKINGS)}>My tickets</button></li>}
        </ul>

        {user && <NotificationBell />}
        {/* Auth area */}
        <div className={styles.auth}>
          {user ? (
            <>
              <div className={styles.userChip}>
                <span className={styles.avatar}>{(user.full_name || user.email)[0].toUpperCase()}</span>
                <span className={styles.greeting}>{user.full_name || user.email.split('@')[0]}</span>
              </div>

              {user.role === 'organizer' && (
                <button className="btn btn-ghost btn-sm" onClick={() => nav(PAGES.ORGANIZER)}>Dashboard</button>
              )}
              <button className="btn btn-ghost btn-sm" onClick={logout}>Log out</button>
            </>
          ) : (
            <>
              <button className="btn btn-ghost btn-sm" onClick={() => { setAuthTab('login'); setAuthOpen(true) }}>Log in</button>
              <button className="btn btn-primary btn-sm" onClick={() => { setAuthTab('signup'); setAuthOpen(true) }}>Sign up ✨</button>
            </>
          )}
        </div>

        {/* Hamburger */}
        <button className={styles.hamburger} aria-label="Menu" aria-expanded={menuOpen} aria-controls="mobile-navigation" onClick={() => setMenuOpen(!menuOpen)}>
          <span /><span /><span />
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div id="mobile-navigation" className={styles.mobileMenu}>
          {user?.role === 'customer' && <button onClick={() => nav(PAGES.BOOKINGS)}>My tickets</button>}
          <button onClick={() => { goHome(); setMenuOpen(false); setTimeout(onExplore, 100) }}>Events</button>
          {user?.role === 'organizer' && (
            <button onClick={() => nav(PAGES.ORGANIZER)}>Dashboard</button>
          )}
          {user ? (
            <button className="btn btn-ghost" onClick={() => { logout(); setMenuOpen(false) }}>Log out</button>
          ) : (
            <>
              <button className="btn btn-ghost" onClick={() => { setAuthTab('login'); setAuthOpen(true); setMenuOpen(false) }}>Log in</button>
              <button className="btn btn-primary" onClick={() => { setAuthTab('signup'); setAuthOpen(true); setMenuOpen(false) }}>Sign up ✨</button>
            </>
          )}
        </div>
      )}
    </nav>
  )
}
