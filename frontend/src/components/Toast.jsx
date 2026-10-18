import { useApp } from '../context/AppContext'

export default function Toast() {
  const { toasts } = useApp()
  return (
    <div className="toast-wrap" aria-live="polite" aria-atomic="false">
      {toasts.map(({ id, message, type }) => (
        <div key={id} className={`toast toast-${type}`}>
          <span>{type === 'success' ? '✅' : '❌'}</span>
          <span>{message}</span>
        </div>
      ))}
    </div>
  )
}
