import { useEffect, useState } from "react";

import { openJobSocket } from "@/lib/ws";

export interface WebSocketMessage {
  event: string;
  data: Record<string, unknown>;
}

export const useWebSocket = () => {
  const [message, setMessage] = useState<WebSocketMessage | null>(null);

  useEffect(() => {
    // Authenticated, self-reconnecting socket (attaches the token and reopens
    // on token refresh); see openJobSocket in @/lib/ws.
    const socket = openJobSocket((data) => {
      try {
        setMessage(JSON.parse(data) as WebSocketMessage);
      } catch {
        setMessage(null);
      }
    });

    return () => {
      socket.close();
    };
  }, []);

  return message;
};
