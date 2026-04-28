/** @ts-check */
/// <reference types="vite/client" />
/**
 * Minimal logging utility for frontend.
 * In development, errors are logged to console for debugging.
 * In production, errors are silently suppressed (they should be
 * communicated to the user via UI alerts/toasts).
 */

const IS_DEV = import.meta.env.DEV

export function logError(scope: string, message: string, err?: unknown): void {
  if (IS_DEV) {
    console.error(`[${scope}] ${message}`, err)
  }
}
