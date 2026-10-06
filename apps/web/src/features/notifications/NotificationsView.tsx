import React, { useEffect, useState } from "react";
import { AXIOS_INSTANCE } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Bell, Check, CheckCheck, Filter, Radio, Sparkles } from "lucide-react";

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

export const NotificationsView: React.FC = () => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [loading, setLoading] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await AXIOS_INSTANCE.get<{
        items: NotificationItem[];
        total: number;
        unread_count: number;
      }>(`/api/v1/notifications?unread_only=${unreadOnly}&page=1&page_size=50`);
      setNotifications(res.data.items);
      setUnreadCount(res.data.unread_count);
    } catch (err) {
      console.error("Erro ao carregar notificações:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [unreadOnly]);

  const handleMarkRead = async (id: string) => {
    try {
      await AXIOS_INSTANCE.patch(`/api/v1/notifications/${id}/read`);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await AXIOS_INSTANCE.post("/api/v1/notifications/mark-all-read");
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error(err);
    }
  };

  const getTypeBadge = (type: string) => {
    switch (type) {
      case "success":
        return <Badge className="bg-green-500 text-white text-[10px]">Sucesso</Badge>;
      case "warning":
        return <Badge className="bg-yellow-500 text-black text-[10px]">Aviso</Badge>;
      case "error":
        return <Badge variant="destructive" className="text-[10px]">Alerta</Badge>;
      default:
        return <Badge variant="secondary" className="text-[10px]">Info</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Bell className="h-6 w-6 text-primary" />
            Central de Notificações
          </h2>
          <p className="text-sm text-muted-foreground">
            Avisos de sistema, eventos assíncronos e atualizações entregues via WebSockets.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setUnreadOnly(!unreadOnly)}
            className="gap-1.5"
          >
            <Filter className="h-4 w-4" />
            {unreadOnly ? "Mostrando Apenas Não Lidas" : "Todas as Notificações"}
          </Button>

          {unreadCount > 0 && (
            <Button size="sm" onClick={handleMarkAllRead} className="gap-1.5">
              <CheckCheck className="h-4 w-4" />
              Marcar Todas como Lidas
            </Button>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 bg-muted/40 p-3 rounded-lg border text-xs text-muted-foreground">
        <Radio className="h-4 w-4 text-green-500 animate-pulse" />
        <span>
          Canal WebSocket ativo em <code>/api/v1/notifications/ws</code> com suporte multitela e reconexão automática.
        </span>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : notifications.length === 0 ? (
        <Card className="text-center py-12 border-dashed">
          <CardContent className="space-y-2">
            <Sparkles className="h-10 w-10 text-muted-foreground mx-auto" />
            <p className="text-sm font-medium text-muted-foreground">
              Você não tem notificações {unreadOnly ? "não lidas" : ""}.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {notifications.map((item) => (
            <Card
              key={item.id}
              className={`transition-all ${
                item.is_read ? "opacity-75 bg-card" : "border-primary/40 bg-primary/5 shadow-sm"
              }`}
            >
              <CardContent className="p-4 flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {getTypeBadge(item.type)}
                    <h4 className="font-semibold text-sm">{item.title}</h4>
                    <span className="text-xs text-muted-foreground">
                      • {new Date(item.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                    {item.message}
                  </p>
                </div>

                {!item.is_read && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 text-xs shrink-0 gap-1 text-primary hover:text-primary"
                    onClick={() => handleMarkRead(item.id)}
                  >
                    <Check className="h-3.5 w-3.5" />
                    Lida
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
