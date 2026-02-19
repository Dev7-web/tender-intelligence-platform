import { useEffect, useState } from "react";

export interface WebSocketMessage {
  event: string;
  data: Record<string, unknown>;
}

export const useWebSocket = () => {
  const [message, setMessage] = useState<WebSocketMessage | null>(null);

  useEffect(() => {
    const wsUrl = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";
    const socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as WebSocketMessage;
        setMessage(parsed);
      } catch {
        setMessage(null);
      }
    };

    return () => {
      socket.close();
    };
  }, []);

  return message;
};
