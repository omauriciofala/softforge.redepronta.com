import uuid
from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from loguru import logger


class NotificationConnectionManager:
    """Gerenciador de conexões WebSocket persistentes para notificações in-app em tempo real."""

    def __init__(self) -> None:
        # Mapeia user_id -> lista de conexões abertas (múltiplas abas/dispositivos do mesmo usuário)
        self._active_connections: dict[uuid.UUID, list[WebSocket]] = defaultdict(list)

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._active_connections[user_id].append(websocket)
        logger.debug(
            f"[NotificationWS] Usuário {user_id} conectado via WebSocket. Total abas ativas: {len(self._active_connections[user_id])}"
        )

    def disconnect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        if user_id in self._active_connections:
            if websocket in self._active_connections[user_id]:
                self._active_connections[user_id].remove(websocket)
            if not self._active_connections[user_id]:
                del self._active_connections[user_id]
        logger.debug(f"[NotificationWS] Conexão WebSocket encerrada para o usuário {user_id}.")

    async def send_personal_notification(
        self,
        user_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> int:
        """Envia mensagem para todas as abas ativas do usuário. Retorna quantidade de sockets entregues."""
        connections = self._active_connections.get(user_id, [])
        if not connections:
            return 0

        stale_sockets: list[WebSocket] = []
        sent_count = 0

        for ws in connections:
            try:
                await ws.send_json(payload)
                sent_count += 1
            except Exception as exc:
                logger.warning(f"[NotificationWS] Falha ao enviar para socket de {user_id}: {exc}")
                stale_sockets.append(ws)

        # Remove conexões mortas
        for ws in stale_sockets:
            self.disconnect(user_id, ws)

        return sent_count

    @property
    def online_users_count(self) -> int:
        return len(self._active_connections)


# Instância global reutilizável
ws_manager = NotificationConnectionManager()
