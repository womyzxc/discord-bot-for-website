"use client";

import { useEffect, useRef, useState, useCallback } from "react";

export interface WebSocketMessage {
  type: string;
  data?: unknown;
  guild_id?: string;
  timestamp?: string;
}

export interface ThreatEvent {
  user_id: string;
  threat_type: string;
  threat_score: number;
  details?: string;
  detected_at: string;
}

export interface SecurityEvent {
  event_type: string;
  user_id?: string;
  target_id?: string;
  action?: string;
  details?: string;
  severity: string;
  timestamp: string;
}

export interface ModerationEvent {
  action: string;
  user_id: string;
  moderator_id: string;
  reason?: string;
  timestamp: string;
}

interface UseWebSocketOptions {
  url?: string;
  guildId?: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  threats: ThreatEvent[];
  securityEvents: SecurityEvent[];
  moderationEvents: ModerationEvent[];
  send: (data: WebSocketMessage) => void;
  subscribe: (guildId: string) => void;
  clearEvents: () => void;
}

const DEFAULT_WS_URL = process.env.NEXT_PUBLIC_BOT_WS_URL || "ws://localhost:8080/ws";

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    url = DEFAULT_WS_URL,
    guildId,
    reconnectInterval = 5000,
    maxReconnectAttempts = 10,
    onOpen,
    onClose,
    onError,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [threats, setThreats] = useState<ThreatEvent[]>([]);
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [moderationEvents, setModerationEvents] = useState<ModerationEvent[]>([]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = guildId ? `${url}/${guildId}` : url;

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log("[WebSocket] Connected to", wsUrl);
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        onOpen?.();

        // Start ping interval to keep connection alive
        pingIntervalRef.current = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: "ping" }));
          }
        }, 30000);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          // Route message to appropriate state based on type
          switch (message.type) {
            case "threat_detected":
            case "threat_blocked":
            case "user_flagged":
              if (message.data) {
                setThreats((prev) => [message.data as ThreatEvent, ...prev].slice(0, 100));
              }
              break;

            case "nuke_attempt":
            case "raid_detected":
            case "spam_detected":
            case "lockdown_started":
            case "lockdown_ended":
              if (message.data) {
                setSecurityEvents((prev) => [
                  { ...(message.data as SecurityEvent), event_type: message.type, timestamp: message.timestamp || new Date().toISOString() },
                  ...prev,
                ].slice(0, 100));
              }
              break;

            case "user_banned":
            case "user_kicked":
            case "user_muted":
            case "user_warned":
              if (message.data) {
                setModerationEvents((prev) => [message.data as ModerationEvent, ...prev].slice(0, 100));
              }
              break;

            case "pong":
              // Heartbeat response, no action needed
              break;

            default:
              console.log("[WebSocket] Unknown message type:", message.type);
          }
        } catch (e) {
          console.error("[WebSocket] Failed to parse message:", e);
        }
      };

      wsRef.current.onclose = () => {
        console.log("[WebSocket] Disconnected");
        setIsConnected(false);
        onClose?.();

        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }

        // Attempt to reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`[WebSocket] Reconnecting in ${reconnectInterval}ms... (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
          reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error("[WebSocket] Error:", error);
        onError?.(error);
      };
    } catch (e) {
      console.error("[WebSocket] Failed to connect:", e);
    }
  }, [url, guildId, reconnectInterval, maxReconnectAttempts, onOpen, onClose, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const send = useCallback((data: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn("[WebSocket] Cannot send - not connected");
    }
  }, []);

  const subscribe = useCallback((newGuildId: string) => {
    send({ type: "subscribe", guild_id: newGuildId } as WebSocketMessage);
  }, [send]);

  const clearEvents = useCallback(() => {
    setThreats([]);
    setSecurityEvents([]);
    setModerationEvents([]);
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    threats,
    securityEvents,
    moderationEvents,
    send,
    subscribe,
    clearEvents,
  };
}

// Export types for use in components
export type { UseWebSocketOptions, UseWebSocketReturn };
