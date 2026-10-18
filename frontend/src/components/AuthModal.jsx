import { errorDetail } from '../lib/booking'
import { useDialog } from '../lib/useDialog'
import { useState, useRef } from 'react'
import { useApp } from '../context/AppContext'
import styles from './AuthModal.module.css'

export default function AuthModal() {
  const { setAuthOpen, doLogin, doSignup, addToast, authTab } = useApp()
  const [tab, setTab]           = useState(authTab)
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole]         = useState('customer')
  const [busy, setBusy]         = useState(false)
  const [err, setErr]           = useState('')

  const lock = useRef(false)
  const close = () => { if (!lock.current) setAuthOpen(false) }
  const dialog = useDialog(close, busy)

  async function submit(e) {
    e.preventDefault()
    if (lock.current) return
    lock.current = true
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
      setErr(errorDetail(ex))
    } finally {
      lock.current = false
      setBusy(false)
    }
  }

  return (
    <dialog ref={dialog} className={styles.modal} aria-labelledby="auth-title">
        {/* Close */}
        <button className={styles.close} onClick={close} disabled={busy} aria-label="Close login">✕</button>

        {/* Header */}
        <div className={styles.header}>
          <span className={styles.logoSmall}>🎟️ Jtickets</span>
          <h2 id="auth-title" className={styles.title}>
            {tab === 'login' ? 'Welcome back! 👋' : 'Join the fun ✨'}
          </h2>
        </div>

        {/* Tabs */}
        <div className={styles.tabs}>
          <button className={`${styles.tab} ${tab === 'login' ? styles.active : ''}`} disabled={busy} onClick={() => setTab('login')}>Log in</button>
          <button className={`${styles.tab} ${tab === 'signup' ? styles.active : ''}`} disabled={busy} onClick={() => setTab('signup')}>Sign up</button>
        </div>

        <form className={styles.form} onSubmit={submit}><fieldset disabled={busy} className={styles.fields}>
          <div className={styles.field}>
            <label htmlFor="auth-email">Email</label>
            <input className="input" id="auth-email" autoComplete="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required />
          </div>
          <div className={styles.field}>
            <label htmlFor="auth-password">Password</label>
            <input className="input" id="auth-password" autoComplete={tab === 'login' ? 'current-password' : 'new-password'} type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min 8 characters" required minLength={8} />
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

          {err && <p role="alert" className={styles.err}>{err}</p>}

          <button className={`btn btn-primary ${styles.submit}`} type="submit" disabled={busy}>
            {busy ? '…' : tab === 'login' ? 'Log in 🚀' : 'Create account ✨'}
          </button>
        </fieldset></form>

        <p className={styles.switch}>
          {tab === 'login'
            ? <>New here? <button disabled={busy} onClick={() => setTab('signup')}>Sign up</button></>
            : <>Already have an account? <button disabled={busy} onClick={() => setTab('login')}>Log in</button></>
          }
        </p>
    </dialog>
  )
}
