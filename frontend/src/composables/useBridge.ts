/**
 * Event listener lifecycle management for pywebvue bridge events.
 *
 * Automatically cleans up listeners when the component unmounts.
 */

import { onUnmounted } from "vue"

type EventCallback = (detail: unknown) => void

/**
 * Register a pywebvue event listener that auto-cleans on component unmount.
 *
 * @param event - Event name without the "pywebvue:" prefix (e.g. "task_progress")
 * @param handler - Callback receiving the event detail payload
 */
export function useBridge() {
  const _listeners: Array<{ event: string; handler: EventListener }> = []

  function on(event: string, callback: EventCallback): void {
    const wrapped: EventListener = (e: Event) => {
      callback((e as CustomEvent).detail)
    }
    window.addEventListener(`pywebvue:${event}`, wrapped)
    _listeners.push({ event, handler: wrapped })
  }

  function off(event: string): void {
    const idx = _listeners.findIndex((l) => l.event === event)
    if (idx !== -1) {
      window.removeEventListener(`pywebvue:${_listeners[idx].event}`, _listeners[idx].handler)
      _listeners.splice(idx, 1)
    }
  }

  function cleanup(): void {
    for (const { event, handler } of _listeners) {
      window.removeEventListener(`pywebvue:${event}`, handler)
    }
    _listeners.length = 0
  }

  onUnmounted(cleanup)

  return { on, off, cleanup }
}
