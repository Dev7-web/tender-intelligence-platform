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

export const connectWs = (onMessage: (event: JobProgressEvent) => void) => {
  const wsUrl = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";
  const socket = new WebSocket(wsUrl);

  socket.onmessage = (evt) => {
    try {
      const data = JSON.parse(evt.data) as JobProgressEvent;
      onMessage(data);
    } catch {
      return;
    }
  };

  return socket;
};
