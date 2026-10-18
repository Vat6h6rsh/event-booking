import { useLayoutEffect, useRef } from 'react'
// Native modal dialogs provide background inertness and keyboard focus containment.
export function useDialog(onClose, blocked = false) {
  const ref = useRef(null)
  const state = useRef({ onClose, blocked })
  state.current = { onClose, blocked }
  useLayoutEffect(() => {
    const trigger = document.activeElement
    const dialog = ref.current
    dialog.showModal()
    const cancel = e => { e.preventDefault(); if (!state.current.blocked) state.current.onClose() }
    dialog.addEventListener('cancel', cancel)
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      dialog.removeEventListener('cancel', cancel)
      dialog.close()
      document.body.style.overflow = previous
      queueMicrotask(() => { if (trigger?.isConnected && !document.querySelector('dialog[open]')) trigger.focus({ preventScroll: true }) })
    }
  }, [])
  return ref
}
