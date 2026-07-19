import { useState, useEffect, useRef } from 'react'
import { createSupportTicket, mySupportTickets, getSupportMessages, sendSupportMessage } from '../lib/api'
import { useApp } from '../context/AppContext'
import styles from './SupportWidget.module.css'

export default function SupportWidget({ onClose }) {
  const { user, addToast } = useApp()
  const [view, setView]       = useState('list')   // list | new | chat
  const [tickets, setTickets] = useState([])
  const [active, setActive]   = useState(null)
  const [messages, setMessages] = useState([])
  const [form, setForm]       = useState({ subject:'', description:'', category:'general', priority:'medium' })
  const [msg, setMsg]         = useState('')
  const [busy, setBusy]       = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    if (!user) return
    mySupportTickets().then(r => setTickets(r.data)).catch(() => {})
  }, [user])

  useEffect(() => {
    if (active) {
      getSupportMessages(active.id).then(r => setMessages(r.data)).catch(() => {})
    }
  }, [active?.id])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior:'smooth' }) }, [messages])

  async function submitTicket(e) {
    e.preventDefault(); setBusy(true)
    try {
      const res = await createSupportTicket(form)
      setTickets(t => [res.data, ...t])
      setActive(res.data); setMessages([]); setView('chat')
      addToast('Support ticket created!')
    } catch { addToast('Failed to create ticket', 'error') }
    finally { setBusy(false) }
  }

  async function submitMsg(e) {
    e.preventDefault(); if (!msg.trim()) return
    setBusy(true)
    try {
      const res = await sendSupportMessage(active.id, msg.trim())
      setMessages(m => [...m, res.data]); setMsg('')
    } catch { addToast('Failed to send message', 'error') }
    finally { setBusy(false) }
  }

  const statusColor = { open:'#22C55E', in_progress:'#F59E0B', resolved:'#3B82F6', closed:'#6B7280' }

  return (
    <div className={styles.widget}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.logo}>💬</span>
          <div>
            <p className={styles.headerTitle}>Jtickets Support</p>
            <p className={styles.headerSub}>We typically reply within a few hours</p>
          </div>
        </div>
        <button className={styles.close} onClick={onClose}>✕</button>
      </div>

      {!user && (
        <div className={styles.noAuth}>
          <p>Please <strong>log in</strong> to access support.</p>
        </div>
      )}

      {user && (
        <>
          <div className={styles.tabs}>
            <button className={`${styles.tab} ${view !== 'new' ? styles.tabActive : ''}`} onClick={() => setView('list')}>My Tickets ({tickets.length})</button>
            <button className={`${styles.tab} ${view === 'new' ? styles.tabActive : ''}`} onClick={() => setView('new')}>+ New Ticket</button>
          </div>

          {/* Ticket list */}
          {view === 'list' && (
            <div className={styles.ticketList}>
              {tickets.length === 0 && <p className={styles.noTickets}>No tickets yet. Need help? Open a new ticket!</p>}
              {tickets.map(t => (
                <button key={t.id} className={styles.ticketItem} onClick={() => { setActive(t); setView('chat') }}>
                  <div className={styles.ticketTop}>
                    <span className={styles.ticketSubject}>{t.subject}</span>
                    <span className={styles.ticketStatus} style={{ color: statusColor[t.status] }}>● {t.status.replace('_', ' ')}</span>
                  </div>
                  <div className={styles.ticketMeta}>
                    <span>{t.category}</span>
                    <span>Priority: {t.priority}</span>
                    <span>{new Date(t.created_at).toLocaleDateString('en-IN')}</span>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* New ticket */}
          {view === 'new' && (
            <form className={styles.newForm} onSubmit={submitTicket}>
              <input className="input" placeholder="Subject *" value={form.subject} required
                onChange={e => setForm(f => ({...f, subject:e.target.value}))} />
              <div className={styles.row2}>
                <select className="input" value={form.category} onChange={e => setForm(f => ({...f, category:e.target.value}))}>
                  {['general','booking','payment','event','venue'].map(c => <option key={c}>{c}</option>)}
                </select>
                <select className="input" value={form.priority} onChange={e => setForm(f => ({...f, priority:e.target.value}))}>
                  {['low','medium','high','urgent'].map(p => <option key={p}>{p}</option>)}
                </select>
              </div>
              <textarea className="input" rows={4} placeholder="Describe your issue in detail…" required
                value={form.description} onChange={e => setForm(f => ({...f, description:e.target.value}))} />
              <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? 'Submitting…' : 'Submit Ticket'}</button>
            </form>
          )}

          {/* Chat */}
          {view === 'chat' && active && (
            <div className={styles.chat}>
              <div className={styles.chatHead}>
                <button className={styles.backBtn} onClick={() => setView('list')}>← Back</button>
                <div>
                  <p className={styles.chatSubject}>{active.subject}</p>
                  <span style={{ color: statusColor[active.status], fontSize:'0.72rem', fontWeight:800 }}>
                    ● {active.status.replace('_', ' ')}
                  </span>
                </div>
              </div>
              <div className={styles.messages}>
                {messages.length === 0 && (
                  <p className={styles.noMsgs}>No messages yet. Describe your issue below and we'll get back to you.</p>
                )}
                {messages.map(m => (
                  <div key={m.id} className={`${styles.msgBubble} ${m.sender_id === user?.id ? styles.msgMe : styles.msgStaff}`}>
                    <p className={styles.msgText}>{m.message}</p>
                    <span className={styles.msgMeta}>
                      {m.is_staff ? '🎭 Support' : '👤 You'} · {new Date(m.created_at).toLocaleTimeString('en-IN', { hour:'2-digit', minute:'2-digit' })}
                    </span>
                  </div>
                ))}
                <div ref={bottomRef} />
              </div>
              {active.status !== 'closed' ? (
                <form className={styles.msgForm} onSubmit={submitMsg}>
                  <input className="input" placeholder="Type a message…" value={msg} onChange={e => setMsg(e.target.value)} />
                  <button type="submit" className="btn btn-primary btn-sm" disabled={busy || !msg.trim()}>Send</button>
                </form>
              ) : (
                <p className={styles.closedNote}>This ticket is closed. Open a new ticket if you need more help.</p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
