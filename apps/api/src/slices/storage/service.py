import re
import uuid
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.errors import AppException, NotFoundException
from src.slices.auth.models import User
from src.slices.storage.models import StoredFile


def sanitize_filename(filename: str) -> str:
    """Sanitiza o nome original do arquivo removendo caracteres perigosos."""
    clean = re.sub(r"[^\w\.-]", "_", filename.strip())
    return clean or "arquivo_anexo"


def get_local_storage_root() -> Path:
    """Retorna o diretório base para armazenamento local de uploads."""
    root = Path(settings.STORAGE_LOCAL_DIR).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_bytes(storage_path: str, data: bytes) -> None:
    """Persiste os bytes no backend configurado (padrão local em dev/testes)."""
    root = get_local_storage_root()
    target = root / storage_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def read_bytes(storage_path: str) -> bytes:
    """Lê os bytes do arquivo a partir do storage."""
    root = get_local_storage_root()
    target = root / storage_path
    if not target.exists():
        raise NotFoundException(message="Arquivo físico não encontrado no storage.")
    return target.read_bytes()


def delete_bytes(storage_path: str) -> None:
    """Remove os bytes físicos do arquivo do storage."""
    root = get_local_storage_root()
    target = root / storage_path
    if target.exists():
        target.unlink()


def build_download_url(file_id: uuid.UUID) -> str:
    """Gera a URL pública/autenticada para download ou streaming do arquivo."""
    return f"{settings.API_V1_STR}/storage/files/{file_id}/download"


async def upload_workspace_file(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str,
    content_type: str,
    data: bytes,
) -> StoredFile:
    """Armazena um novo arquivo associado ao workspace validando tamanho e metadados."""
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise AppException(
            message=f"Arquivo excede o limite máximo permitido de {settings.MAX_UPLOAD_SIZE_MB}MB.",
            status_code=413,
            code="FILE_TOO_LARGE",
        )

    file_id = uuid.uuid4()
    clean_name = sanitize_filename(filename)
    storage_path = f"workspaces/{workspace_id}/{file_id}_{clean_name}"

    save_bytes(storage_path, data)

    stored_file = StoredFile(
        id=file_id,
        workspace_id=workspace_id,
        uploaded_by_user_id=user_id,
        filename=clean_name,
        content_type=content_type or "application/octet-stream",
        file_size_bytes=len(data),
        storage_backend=settings.STORAGE_BACKEND,
        storage_path=storage_path,
        is_public=False,
    )
    session.add(stored_file)
    await session.commit()
    await session.refresh(stored_file)
    return stored_file


async def upload_user_avatar(
    session: AsyncSession,
    user: User,
    filename: str,
    content_type: str,
    data: bytes,
) -> tuple[StoredFile, str]:
    """Armazena a imagem de avatar do usuário e atualiza seu perfil com a URL pública."""
    max_bytes = 5 * 1024 * 1024  # 5MB para avatares
    if len(data) > max_bytes:
        raise AppException(
            message="Imagem de perfil excede o limite de 5MB.",
            status_code=413,
            code="FILE_TOO_LARGE",
        )

    file_id = uuid.uuid4()
    clean_name = sanitize_filename(filename)
    storage_path = f"avatars/{user.id}/{file_id}_{clean_name}"

    save_bytes(storage_path, data)

    stored_file = StoredFile(
        id=file_id,
        workspace_id=None,
        uploaded_by_user_id=user.id,
        filename=clean_name,
        content_type=content_type or "image/png",
        file_size_bytes=len(data),
        storage_backend=settings.STORAGE_BACKEND,
        storage_path=storage_path,
        is_public=True,
    )
    session.add(stored_file)

    download_url = build_download_url(file_id)
    user.avatar_url = download_url
    session.add(user)

    await session.commit()
    await session.refresh(stored_file)
    return stored_file, download_url


async def get_stored_file(
    session: AsyncSession,
    file_id: uuid.UUID,
) -> StoredFile:
    """Busca o registro do arquivo no banco de dados."""
    stmt = select(StoredFile).where(StoredFile.id == file_id)
    res = await session.execute(stmt)
    file = res.scalar_one_or_none()
    if not file:
        raise NotFoundException(message="Arquivo não encontrado.")
    return file


async def list_workspace_files(
    session: AsyncSession,
    workspace_id: uuid.UUID,
) -> list[StoredFile]:
    """Lista todos os arquivos anexados ao workspace."""
    stmt = (
        select(StoredFile)
        .where(StoredFile.workspace_id == workspace_id)
        .order_by(StoredFile.created_at.desc())
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def count_workspace_files(
    session: AsyncSession,
    workspace_id: uuid.UUID,
) -> int:
    """Retorna o total de arquivos armazenados no workspace."""
    stmt = select(func.count(StoredFile.id)).where(StoredFile.workspace_id == workspace_id)
    res = await session.execute(stmt)
    return res.scalar() or 0


async def delete_workspace_file(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    file_id: uuid.UUID,
) -> StoredFile:
    """Remove o arquivo físico e o registro no banco de dados."""
    stmt = select(StoredFile).where(
        StoredFile.id == file_id,
        StoredFile.workspace_id == workspace_id,
    )
    res = await session.execute(stmt)
    file = res.scalar_one_or_none()
    if not file:
        raise NotFoundException(message="Arquivo não encontrado no workspace.")

    delete_bytes(file.storage_path)
    await session.delete(file)
    await session.commit()
    return file
