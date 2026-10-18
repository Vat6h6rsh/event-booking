import { useApp, PAGES } from '../context/AppContext'
import styles from './Footer.module.css'

export default function Footer({ onSupport }) {
  const { setPage, goHome, setCategory, user, setAuthOpen } = useApp()

  return (
    <footer className={styles.footer}>
      <div className={`container ${styles.inner}`}>
        {/* Brand */}
        <div className={styles.brand}>
          <button className={styles.logo} onClick={goHome}>🎟️ Jtickets</button>
          <p>Where every moment becomes magical. ✨</p>
          <div className={styles.socials}>
            {['🎵', '📸', '🐦', '💜'].map((e, i) => (
              <span key={i} className={styles.socialBtn}>{e}</span>
            ))}
          </div>
        </div>

        {/* Explore */}
        <div className={styles.col}>
          <h4 className={styles.colTitle}>Explore</h4>
          {['Music', 'Movies', 'Festival', 'Sports', 'Food', 'Comedy'].map(c => (
            <button key={c} className={styles.link} onClick={() => { setCategory(c); goHome() }}>{c} Events</button>
          ))}
        </div>

        {/* Company */}
        <div className={styles.col}>
          <h4 className={styles.colTitle}>Platform</h4>
          <button className={styles.link} onClick={() => user?.role === 'organizer' ? setPage(PAGES.ORGANIZER) : setAuthOpen(true)}>Organizer Dashboard</button>
          <button className={styles.link} onClick={onSupport}>Chat with Us</button>
        </div>

        {/* Legal */}
        <div className={styles.col}>
          <h4 className={styles.colTitle}>Legal</h4>
          <button className={styles.link} onClick={() => setPage(PAGES.TERMS)}>Terms of Use</button>
          <button className={styles.link} onClick={() => setPage(PAGES.PRIVACY)}>Privacy Policy</button>
          <button className={styles.link} onClick={onSupport}>Contact Support</button>
        </div>
      </div>

      <div className={styles.bottom}>
        <span>© 2026 Jtickets. Made with 💜 in India.</span>
        <span className={styles.floaties}>🎵 🎬 🎪 🎉 🌟</span>
      </div>
    </footer>
  )
}
