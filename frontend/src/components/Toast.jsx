import { useApp } from '../context/AppContext'

export default function Toast() {
  const { toasts } = useApp()
  if (!toasts.length) return null
  return (
    <div className="toast-wrap">
      {toasts.map(({ id, message, type }) => (
        <div key={id} className={`toast toast-${type}`}>
          <span>{type === 'success' ? '✅' : '❌'}</span>
          <span>{message}</span>
        </div>
      ))}
    </div>
  )
}
