import { AUTH_CLEARED_EVENT, AUTH_TOKEN_EVENT, getToken } from "@/lib/auth";

export interface JobProgressEvent {
  type: string;
  job: string;
  job_id: string;
  status: "started" | "progress" | "completed" | "failed";
  progress?: {
    current: number;
    total: number;
    percent: number;
  };
  message?: string;
  ts?: string;
}

export interface ReconnectingSocket {
  close: () => void;
}

const NORMAL_CLOSURE = 1000;
// Server rejects the connection with this code when the token is missing or
// invalid (see the /ws server-side auth fix).
const AUTH_REJECTED_CODE = 4001;
const INITIAL_BACKOFF_MS = 1000;
const MAX_BACKOFF_MS = 15000;

const baseWsUrl = () => import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";

// The /ws endpoint authenticates via a `token` query parameter. Browsers can't
// set headers on a WebSocket handshake, so the JWT is passed in the URL.
const buildWsUrl = (token: string) => {
  const base = baseWsUrl();
  const separator = base.includes("?") ? "&" : "?";
  return `${base}${separator}token=${encodeURIComponent(token)}`;
};

/**
 * Opens an authenticated /ws connection and keeps it alive:
 *  - attaches the current auth token as a query parameter,
 *  - reconnects with the new token when it is refreshed (AUTH_TOKEN_EVENT),
 *  - drops the socket on logout / session expiry (AUTH_CLEARED_EVENT),
 *  - reconnects with backoff on unexpected drops, but not on an auth
 *    rejection (4001), where it waits for a fresh token instead.
 *
 * Raw message payloads are handed to `onData`; callers parse them.
 */
export const openJobSocket = (onData: (data: string) => void): ReconnectingSocket => {
  let socket: WebSocket | null = null;
  let stopped = false; // caller has closed the socket for good
  let reconnectTimer: number | undefined;
  let backoff = INITIAL_BACKOFF_MS;

  function clearReconnect() {
    if (reconnectTimer !== undefined) {
      window.clearTimeout(reconnectTimer);
      reconnectTimer = undefined;
    }
  }

  function teardownSocket() {
    if (socket) {
      // Detach handlers so this deliberate close doesn't trigger a reconnect.
      socket.onopen = null;
      socket.onmessage = null;
      socket.onclose = null;
      try {
        socket.close(NORMAL_CLOSURE);
      } catch {
        /* already closing */
      }
      socket = null;
    }
  }

  function scheduleReconnect() {
    if (stopped) return;
    clearReconnect();
    reconnectTimer = window.setTimeout(() => {
      backoff = Math.min(backoff * 2, MAX_BACKOFF_MS);
      connect();
    }, backoff);
  }

  function connect() {
    if (stopped) return;
    clearReconnect();

    const token = getToken();
    if (!token) {
      // Not authenticated yet; the server would reject with 4001. Wait for an
      // AUTH_TOKEN_EVENT to connect once a token is available.
      return;
    }

    const ws = new WebSocket(buildWsUrl(token));
    socket = ws;

    ws.onopen = () => {
      backoff = INITIAL_BACKOFF_MS; // reset after a successful connection
    };

    ws.onmessage = (evt) => {
      onData(evt.data);
    };

    ws.onclose = (evt) => {
      if (socket === ws) socket = null;
      if (stopped) return;
      // Reconnecting with the same rejected token would loop; wait for a
      // refreshed token (AUTH_TOKEN_EVENT) instead.
      if (evt.code === AUTH_REJECTED_CODE) return;
      scheduleReconnect();
    };
  }

  function handleTokenChange() {
    // Token refreshed or user (re)authenticated: reconnect with the new token.
    backoff = INITIAL_BACKOFF_MS;
    teardownSocket();
    connect();
  }

  function handleAuthCleared() {
    // Logged out / session expired: drop the socket and wait for a new token.
    clearReconnect();
    teardownSocket();
  }

  window.addEventListener(AUTH_TOKEN_EVENT, handleTokenChange);
  window.addEventListener(AUTH_CLEARED_EVENT, handleAuthCleared);
  connect();

  return {
    close() {
      stopped = true;
      clearReconnect();
      teardownSocket();
      window.removeEventListener(AUTH_TOKEN_EVENT, handleTokenChange);
      window.removeEventListener(AUTH_CLEARED_EVENT, handleAuthCleared);
    },
  };
};

export const connectWs = (
  onMessage: (event: JobProgressEvent) => void,
): ReconnectingSocket =>
  openJobSocket((data) => {
    try {
      onMessage(JSON.parse(data) as JobProgressEvent);
    } catch {
      /* ignore malformed frames */
    }
  });
