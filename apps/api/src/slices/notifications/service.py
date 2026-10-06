import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundException
from src.slices.notifications.connection_manager import ws_manager
from src.slices.notifications.models import Notification


async def create_and_send_notification(
    session: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    message: str,
    category: str = "general",
    workspace_id: uuid.UUID | None = None,
    action_url: str | None = None,
) -> Notification:
    """Persiste a notificação no banco de dados e a entrega imediatamente via WebSocket se o usuário estiver online."""
    notification = Notification(
        user_id=user_id,
        workspace_id=workspace_id,
        title=title,
        message=message,
        category=category,
        action_url=action_url,
        is_read=False,
    )
    session.add(notification)
    await session.commit()
    await session.refresh(notification)

    # Disparo em tempo real via WebSocket
    ws_payload = {
        "event": "notification.received",
        "notification": {
            "id": str(notification.id),
            "user_id": str(notification.user_id),
            "workspace_id": str(notification.workspace_id) if notification.workspace_id else None,
            "title": notification.title,
            "message": notification.message,
            "category": notification.category,
            "action_url": notification.action_url,
            "is_read": notification.is_read,
            "created_at": notification.created_at.isoformat(),
        },
    }
    await ws_manager.send_personal_notification(user_id, ws_payload)

    return notification


async def list_user_notifications(
    session: AsyncSession,
    user_id: uuid.UUID,
    unread_only: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Notification], int, int]:
    """Lista notificações do usuário com suporte a paginação e contagem de pendências."""
    base_query = select(Notification).where(Notification.user_id == user_id)

    if unread_only:
        base_query = base_query.where(Notification.is_read == False)  # noqa: E712

    # Contagem total de itens correspondentes
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    # Contagem total de não lidas para o sino
    unread_query = select(func.count()).where(
        Notification.user_id == user_id,
        Notification.is_read == False,  # noqa: E712
    )
    unread_result = await session.execute(unread_query)
    unread_count = unread_result.scalar_one()

    # Paginação
    query = (
        base_query.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(query)
    items = list(result.scalars().all())

    return items, total, unread_count


async def get_unread_count(session: AsyncSession, user_id: uuid.UUID) -> int:
    """Retorna o número de notificações não lidas de um usuário."""
    query = select(func.count()).where(
        Notification.user_id == user_id,
        Notification.is_read == False,  # noqa: E712
    )
    result = await session.execute(query)
    return result.scalar_one()


async def mark_as_read(
    session: AsyncSession,
    notification_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Notification:
    """Marca uma notificação individual como lida garantindo posse pelo usuário."""
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == user_id,
    )
    result = await session.execute(stmt)
    notification = result.scalar_one_or_none()

    if not notification:
        raise NotFoundException(message="Notificação não encontrada.")

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(notification)

    return notification


async def mark_all_as_read(session: AsyncSession, user_id: uuid.UUID) -> int:
    """Marca todas as notificações pendentes do usuário como lidas em batch."""
    now = datetime.now(UTC)
    stmt = (
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .values(is_read=True, read_at=now)
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount or 0
