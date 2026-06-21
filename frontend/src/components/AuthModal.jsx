import { useState } from 'react'
import { useApp } from '../context/AppContext'
import styles from './AuthModal.module.css'

export default function AuthModal() {
  const { setAuthOpen, doLogin, doSignup, addToast, setBookingEvent } = useApp()
  const [tab, setTab]           = useState('login')
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole]         = useState('customer')
  const [busy, setBusy]         = useState(false)
  const [err, setErr]           = useState('')

  async function submit(e) {
    e.preventDefault()
    setErr('')
    setBusy(true)
    try {
      if (tab === 'login') {
        await doLogin(email, password)
        addToast('Welcome back! 🎉')
      } else {
        await doSignup(email, password, role)
        addToast('Account created! 🌟')
      }
      setAuthOpen(false)
    } catch (ex) {
      const msg = ex.response?.data?.detail || 'Something went wrong'
      setErr(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="overlay" onClick={() => setAuthOpen(false)}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        {/* Close */}
        <button className={styles.close} onClick={() => setAuthOpen(false)}>✕</button>

        {/* Header */}
        <div className={styles.header}>
          <span className={styles.logoSmall}>🎟️ Jtickets</span>
          <h2 className={styles.title}>
            {tab === 'login' ? 'Welcome back! 👋' : 'Join the fun ✨'}
          </h2>
        </div>

        {/* Tabs */}
        <div className={styles.tabs}>
          <button className={`${styles.tab} ${tab === 'login' ? styles.active : ''}`} onClick={() => setTab('login')}>Log in</button>
          <button className={`${styles.tab} ${tab === 'signup' ? styles.active : ''}`} onClick={() => setTab('signup')}>Sign up</button>
        </div>

        <form className={styles.form} onSubmit={submit}>
          <div className={styles.field}>
            <label>Email</label>
            <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required />
          </div>
          <div className={styles.field}>
            <label>Password</label>
            <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min 8 characters" required minLength={8} />
          </div>

          {tab === 'signup' && (
            <div className={styles.roleWrap}>
              {[{ val: 'customer', emoji: '🌟', label: 'I want to attend events' },
                { val: 'organizer', emoji: '🎪', label: 'I want to create events' },
              ].map(({ val, emoji, label }) => (
                <label key={val} className={`${styles.roleCard} ${role === val ? styles.roleActive : ''}`}>
                  <input type="radio" name="role" value={val} checked={role === val} onChange={() => setRole(val)} />
                  <span className={styles.roleEmoji}>{emoji}</span>
                  <span className={styles.roleLabel}>{label}</span>
                </label>
              ))}
            </div>
          )}

          {err && <p className={styles.err}>{err}</p>}

          <button className={`btn btn-primary ${styles.submit}`} type="submit" disabled={busy}>
            {busy ? '…' : tab === 'login' ? 'Log in 🚀' : 'Create account ✨'}
          </button>
        </form>

        <p className={styles.switch}>
          {tab === 'login'
            ? <>New here? <button onClick={() => setTab('signup')}>Sign up</button></>
            : <>Already have an account? <button onClick={() => setTab('login')}>Log in</button></>
          }
        </p>
      </div>
    </div>
  )
}
