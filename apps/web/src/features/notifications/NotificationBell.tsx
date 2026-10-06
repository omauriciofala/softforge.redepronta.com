import React, { useEffect, useState } from "react";
import { AXIOS_INSTANCE } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Bell, CheckCheck, Sparkles } from "lucide-react";

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

export interface NotificationBellProps {
  onOpenFullView?: () => void;
}

export const NotificationBell: React.FC<NotificationBellProps> = ({ onOpenFullView }) => {
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [isOpen, setIsOpen] = useState(false);
  const [recentNotifications, setRecentNotifications] = useState<NotificationItem[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  const fetchUnreadCount = async () => {
    try {
      const res = await AXIOS_INSTANCE.get<{ unread_count: number }>(
        "/api/v1/notifications/unread-count"
      );
      setUnreadCount(res.data.unread_count);
    } catch (err) {
      // Falha silenciosa
    }
  };

  const fetchRecent = async () => {
    try {
      const res = await AXIOS_INSTANCE.get<{ items: NotificationItem[] }>(
        "/api/v1/notifications?page=1&page_size=5"
      );
      setRecentNotifications(res.data.items);
    } catch (err) {
      // Falha silenciosa
    }
  };

  // Conexão WebSocket para receber notificações push em tempo real
  useEffect(() => {
    const token = localStorage.getItem("softforge_access_token");
    if (!token) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host.includes(":5173") ? "localhost:8000" : window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/notifications/ws?token=${token}`;

    let ws: WebSocket | null = null;
    let pingInterval: any = null;

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        pingInterval = setInterval(() => {
          if (ws?.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }));
          }
        }, 25000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "pong") return;

          // Nova notificação recebida em tempo real
          setUnreadCount((prev) => prev + 1);
          setRecentNotifications((prev) => [data, ...prev.slice(0, 4)]);
        } catch (e) {
          // ignora ping
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        clearInterval(pingInterval);
      };

      ws.onerror = () => {
        setIsConnected(false);
      };
    } catch (err) {
      setIsConnected(false);
    }

    fetchUnreadCount();

    return () => {
      clearInterval(pingInterval);
      if (ws) ws.close();
    };
  }, []);

  const handleToggle = () => {
    if (!isOpen) {
      fetchRecent();
    }
    setIsOpen(!isOpen);
  };

  const handleMarkAllRead = async () => {
    try {
      await AXIOS_INSTANCE.post("/api/v1/notifications/mark-all-read");
      setUnreadCount(0);
      setRecentNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        onClick={handleToggle}
        className="relative h-9 w-9 p-0 rounded-full hover:bg-muted"
        title={isConnected ? "WebSocket Ativo (Tempo Real)" : "Notificações"}
      >
        <Bell className="h-4 w-4 text-foreground" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white shadow">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </Button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 rounded-xl border bg-card p-3 shadow-xl z-50 text-foreground animate-in fade-in zoom-in-95">
          <div className="flex items-center justify-between border-b pb-2 mb-2">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold uppercase tracking-wider">Notificações</span>
              <span
                className={`h-2 w-2 rounded-full ${isConnected ? "bg-green-500" : "bg-gray-400"}`}
                title={isConnected ? "WebSocket Conectado" : "Offline"}
              />
            </div>
            {unreadCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleMarkAllRead}
                className="h-6 text-[11px] px-1.5 gap-1 text-muted-foreground hover:text-foreground"
              >
                <CheckCheck className="h-3 w-3" />
                Marcar lidas
              </Button>
            )}
          </div>

          <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
            {recentNotifications.length === 0 ? (
              <div className="py-6 text-center text-xs text-muted-foreground space-y-1">
                <Sparkles className="h-6 w-6 text-muted-foreground mx-auto" />
                <p>Nenhuma notificação recente.</p>
              </div>
            ) : (
              recentNotifications.map((n) => (
                <div
                  key={n.id}
                  className={`p-2 rounded-lg text-xs transition-colors ${
                    n.is_read ? "bg-muted/30" : "bg-primary/10 border-l-2 border-primary"
                  }`}
                >
                  <p className="font-semibold truncate">{n.title}</p>
                  <p className="text-[11px] text-muted-foreground line-clamp-2 mt-0.5">{n.message}</p>
                  <span className="text-[9px] text-muted-foreground mt-1 block">
                    {new Date(n.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
              ))
            )}
          </div>

          {onOpenFullView && (
            <div className="border-t pt-2 mt-2 text-center">
              <Button
                variant="link"
                size="sm"
                className="h-6 text-xs text-primary p-0"
                onClick={() => {
                  setIsOpen(false);
                  onOpenFullView();
                }}
              >
                Ver Central de Notificações Completa →
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
