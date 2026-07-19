import { useEffect, useRef, useState } from 'react'
import { useApp, PAGES } from '../context/AppContext'
import NotificationBell from './NotificationBell'
import styles from './Navbar.module.css'

export default function Navbar({ onExplore }) {
  const { user, logout, setAuthOpen, page, setPage, goHome } = useApp()
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const navRef = useRef(null)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  function nav(pg) { setPage(pg); setMenuOpen(false); window.scrollTo({ top:0, behavior:'smooth' }) }

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
            <li><button onClick={() => nav(PAGES.ORGANIZER)}>Dashboard</button></li>
          )}
        </ul>

        {/* Auth area */}
        <div className={styles.auth}>
          {user ? (
            <>
              <span className={styles.greeting}>
                {user.role === 'organizer' ? '🎪' : '🌟'} {user.full_name || user.email.split('@')[0]}
              </span>
              <NotificationBell />
              {user.role === 'organizer' && (
                <button className="btn btn-ghost btn-sm" onClick={() => nav(PAGES.ORGANIZER)}>Dashboard</button>
              )}
              <button className="btn btn-ghost btn-sm" onClick={logout}>Log out</button>
            </>
          ) : (
            <>
              <button className="btn btn-ghost btn-sm" onClick={() => setAuthOpen(true)}>Log in</button>
              <button className="btn btn-primary btn-sm" onClick={() => setAuthOpen(true)}>Sign up ✨</button>
            </>
          )}
        </div>

        {/* Hamburger */}
        <button className={styles.hamburger} aria-label="Menu" onClick={() => setMenuOpen(!menuOpen)}>
          <span /><span /><span />
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className={styles.mobileMenu}>
          <button onClick={() => { goHome(); setMenuOpen(false); setTimeout(onExplore, 100) }}>Events</button>
          {user?.role === 'organizer' && (
            <button onClick={() => nav(PAGES.ORGANIZER)}>Dashboard</button>
          )}
          {user ? (
            <button className="btn btn-ghost" onClick={() => { logout(); setMenuOpen(false) }}>Log out</button>
          ) : (
            <>
              <button className="btn btn-ghost" onClick={() => { setAuthOpen(true); setMenuOpen(false) }}>Log in</button>
              <button className="btn btn-primary" onClick={() => { setAuthOpen(true); setMenuOpen(false) }}>Sign up ✨</button>
            </>
          )}
        </div>
      )}
    </nav>
  )
}
