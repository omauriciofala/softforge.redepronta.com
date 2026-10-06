import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import decode_token
from src.slices.auth.dependencies import get_current_user
from src.slices.auth.models import User
from src.slices.notifications.connection_manager import ws_manager
from src.slices.notifications.schemas import (
    MarkAllReadResponse,
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from src.slices.notifications.service import (
    get_unread_count,
    list_user_notifications,
    mark_all_as_read,
    mark_as_read,
)

router = APIRouter(prefix="/notifications", tags=["Notificações In-App"])


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="Listar notificações do usuário",
    description="Retorna a lista paginada de notificações in-app do usuário autenticado.",
)
async def list_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    unread_only: bool = Query(False, description="Filtrar apenas notificações não lidas"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
) -> NotificationListResponse:
    items, total, unread_count = await list_user_notifications(
        session=session,
        user_id=current_user.id,
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(item) for item in items],
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="Obter contador de notificações não lidas",
    description="Retorna a quantidade de notificações pendentes de leitura para exibição no badge do sino.",
)
async def get_unread_badge(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UnreadCountResponse:
    count = await get_unread_count(session, current_user.id)
    return UnreadCountResponse(unread_count=count)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Marcar notificação como lida",
    description="Atualiza o estado de leitura de uma notificação específica.",
)
async def mark_single_read(
    notification_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationResponse:
    notification = await mark_as_read(session, notification_id, current_user.id)
    return NotificationResponse.model_validate(notification)


@router.post(
    "/mark-all-read",
    response_model=MarkAllReadResponse,
    summary="Marcar todas as notificações como lidas",
    description="Atualiza todas as notificações não lidas do usuário para o estado de lidas.",
)
async def mark_all_notifications_read(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MarkAllReadResponse:
    marked = await mark_all_as_read(session, current_user.id)
    return MarkAllReadResponse(marked_count=marked)


@router.websocket("/ws")
async def websocket_notifications_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT Access Token para autenticação do canal"),
) -> None:
    """Canal WebSocket Full-Duplex para entrega de notificações em tempo real."""
    try:
        payload = decode_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        user_id = uuid.UUID(user_id_str)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect(user_id, websocket)

    try:
        while True:
            # Mantém conexão aberta e responde pings do cliente
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
    except Exception:
        ws_manager.disconnect(user_id, websocket)
