// js/api.js
// All communication with the FastAPI backend lives here.
// Nothing else should call fetch() or new WebSocket() directly.

const API_BASE = `${window.location.protocol}//${window.location.host}`;
const WS_BASE  = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`;

// ── Health ────────────────────────────────────────────────────────────────────

/**
 * Returns true if the API is reachable, false otherwise.
 */
export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/`, { signal: AbortSignal.timeout(3000) });
    return res.ok;
  } catch {
    return false;
  }
}

// ── Settings ──────────────────────────────────────────────────────────────────

/**
 * Fetches the current settings object from the API.
 * @returns {Promise<object>}
 */
export async function getSettings() {
  const res = await fetch(`${API_BASE}/settings/`);
  if (!res.ok) throw new Error(`Failed to fetch settings: ${res.statusText}`);
  return res.json();
}

/**
 * Pushes a full settings object to the API.
 * @param {object} data
 * @returns {Promise<{success: boolean, detail: string}>}
 */
export async function postSettings(data) {
  const res = await fetch(`${API_BASE}/settings/`, {
    method: 'POST',
    headers: {
      'settings-json': JSON.stringify(data),
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Run (WebSocket) ───────────────────────────────────────────────────────────

/**
 * Opens a WebSocket to /run/ and streams log frames.
 *
 * @param {object}   options
 * @param {string}   options.task           - Task description
 * @param {string}   [options.modeOverride] - 'planner' | 'autonomy' | null
 * @param {function} options.onMessage      - Called with each parsed frame object
 * @param {function} options.onDone         - Called when run completes (status=done)
 * @param {function} options.onError        - Called with error message string
 * @param {function} options.onClose        - Called when socket closes (any reason)
 *
 * @returns {{ cancel: function }} - Call cancel() to abort the run
 */
export function startRun({ task, modeOverride, onMessage, onDone, onError, onClose }) {
  const params = new URLSearchParams({ task });
  if (modeOverride) params.set('mode_override', modeOverride);

  const url = `${WS_BASE}/run/?${params}`;
  const ws  = new WebSocket(url);

  ws.addEventListener('message', (event) => {
    let frame;
    try {
      frame = JSON.parse(event.data);
    } catch {
      onMessage?.({ type: 'stdout', level: 'INFO', message: event.data, ts: new Date().toISOString() });
      return;
    }

    if (frame.type === 'status') {
      if (frame.status === 'done') {
        onDone?.(frame.message);
      } else if (frame.status === 'error') {
        onError?.(frame.message);
      }
    } else {
      onMessage?.(frame);
    }
  });

  ws.addEventListener('error', () => {
    onError?.('WebSocket connection error. Is the API running?');
  });

  ws.addEventListener('close', (event) => {
    onClose?.(event.code, event.reason);
  });

  return {
    cancel() {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close(1000, 'Cancelled by user');
      }
    },
  };
}
