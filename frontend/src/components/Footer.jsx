import styles from './Footer.module.css'

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={`container ${styles.inner}`}>
        {/* Brand */}
        <div className={styles.brand}>
          <span className={styles.logo}>🎟️ Jtickets</span>
          <p>Where every moment becomes magical. ✨</p>
          <div className={styles.socials}>
            {['🎵', '📸', '🐦', '💜'].map((e, i) => (
              <a key={i} href="#" className={styles.socialBtn}>{e}</a>
            ))}
          </div>
        </div>

        {/* Links */}
        {[
          { heading: 'Explore', links: ['All Events', 'Music', 'Movies', 'Get-togethers', 'Festivals'] },
          { heading: 'Company', links: ['About Us', 'Blog', 'Careers', 'Press'] },
          { heading: 'Support', links: ['Help Center', 'Contact Us', 'Privacy Policy', 'Terms of Use'] },
        ].map(({ heading, links }) => (
          <div key={heading} className={styles.col}>
            <h4 className={styles.colTitle}>{heading}</h4>
            {links.map((l) => <a key={l} href="#" className={styles.link}>{l}</a>)}
          </div>
        ))}
      </div>

      <div className={styles.bottom}>
        <span>© 2026 Jtickets. Made with 💜 in India.</span>
        <span className={styles.floaties}>🎵 🎬 🎪 🎉 🌟</span>
      </div>
    </footer>
  )
}
