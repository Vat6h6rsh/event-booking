import { useEffect, useRef, useState } from 'react'
import { useApp } from '../context/AppContext'
import styles from './Navbar.module.css'

export default function Navbar({ onExplore }) {
  const { user, logout, setAuthOpen } = useApp()
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const navRef = useRef(null)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <nav ref={navRef} className={`${styles.nav} ${scrolled ? styles.scrolled : ''}`}>
      <div className={styles.inner}>
        {/* Logo */}
        <a href="#" className={styles.logo} onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }) }}>
          <span className={styles.logoIcon}>🎟️</span>
          <span className={styles.logoText}>Jtickets</span>
        </a>

        {/* Nav links (desktop) */}
        <ul className={styles.links}>
          <li><a href="#events" onClick={onExplore}>Events</a></li>
          <li><a href="#how">How it works</a></li>
          {user?.role === 'customer' && <li><a href="#events">My Bookings</a></li>}
        </ul>

        {/* Auth area (desktop) */}
        <div className={styles.auth}>
          {user ? (
            <>
              <span className={styles.greeting}>
                {user.role === 'organizer' ? '🎪' : '🌟'} {user.email.split('@')[0]}
              </span>
              <button className="btn btn-ghost btn-sm" onClick={logout}>Logout</button>
            </>
          ) : (
            <>
              <button className="btn btn-ghost btn-sm" onClick={() => setAuthOpen(true)}>Log in</button>
              <button className="btn btn-primary btn-sm" onClick={() => setAuthOpen(true)}>Sign up ✨</button>
            </>
          )}
        </div>

        {/* Hamburger (mobile) */}
        <button className={styles.hamburger} aria-label="Menu" onClick={() => setMenuOpen(!menuOpen)}>
          <span /><span /><span />
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className={styles.mobileMenu}>
          <a href="#events" onClick={() => setMenuOpen(false)}>Events</a>
          <a href="#how" onClick={() => setMenuOpen(false)}>How it works</a>
          {user ? (
            <button className="btn btn-ghost" onClick={() => { logout(); setMenuOpen(false) }}>Logout</button>
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
