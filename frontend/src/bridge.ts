/** Core bridge functions for communicating with the Python backend. */

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}

const BRIDGE_CALL_TIMEOUT_MS = 30_000

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return Promise.race([
    promise,
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(`Bridge call timed out after ${ms}ms`)), ms)
    ),
  ]);
}

function getRawApi(): PyWebViewApi {
  const pw = window.pywebview;
  if (!pw || !pw.api) {
    throw new Error("pywebview API not available. Wait for pywebview to initialize.");
  }
  return pw.api;
}

/**
 * Poll until the pywebview bridge is ready.
 * Returns a promise that resolves when ``window.pywebview.api`` is populated
 * AND at least one exposed method is callable.
 */
export function waitForPyWebView(timeout = 10_000): Promise<void> {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const check = () => {
      try {
        const api = window.pywebview?.api;
        // Verify the api proxy has resolved its methods
        if (api && typeof (api as any).setup_ffmpeg === "function") {
          resolve();
          return;
        }
      } catch {
        // api might not be fully ready yet
      }
      if (Date.now() - start > timeout) {
        reject(new Error("pywebview bridge did not initialize within timeout"));
        return;
      }
      setTimeout(check, 100);
    };
    check();
  });
}

/**
 * Call an ``@expose``-decorated Python method and return the typed result.
 *
 * ```ts
 * const res = await call<string[]>("get_items")
 * if (res.success) console.log(res.data)
 * ```
 */
export async function call<T = unknown>(
  method: string,
  ...args: unknown[]
): Promise<ApiResponse<T>> {
  const api = getRawApi();
  const fn = api[method as keyof typeof api];
  if (typeof fn !== "function") {
    return { success: false, error: `Method '${method}' not found on bridge` };
  }
  return withTimeout(fn(...args) as Promise<ApiResponse<T>>, BRIDGE_CALL_TIMEOUT_MS)
}

/**
 * Listen for events dispatched by ``Bridge._emit()`` from the Python side.
 *
 * Event names are prefixed with ``pywebvue:``. Returns a cleanup function
 * that removes the listener.
 *
 * ```ts
 * const off = onEvent<{ percent: number }>("progress", (detail) => {
 *   console.log(detail.percent)
 * })
 * // later:
 * off()
 * ```
 */
export function onEvent<T = unknown>(
  name: string,
  handler: (detail: T) => void,
): () => void {
  const event = `pywebvue:${name}`;
  const listener = (e: Event) => {
    handler((e as CustomEvent).detail);
  };
  window.addEventListener(event, listener);
  return () => window.removeEventListener(event, listener);
}
