import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.errors import ForbiddenException
from src.slices.audit.service import log_audit_event
from src.slices.auth.dependencies import get_current_user
from src.slices.auth.models import User
from src.slices.storage.schemas import (
    AvatarUploadResponse,
    StoredFileListResponse,
    StoredFileResponse,
)
from src.slices.storage.service import (
    build_download_url,
    count_workspace_files,
    delete_workspace_file,
    get_stored_file,
    list_workspace_files,
    read_bytes,
    upload_user_avatar,
    upload_workspace_file,
)
from src.slices.webhooks.service import trigger_webhook_event
from src.slices.workspaces.dependencies import require_workspace_role
from src.slices.workspaces.models import WorkspaceMember, WorkspaceRole

router = APIRouter(tags=["Armazenamento & Storage de Arquivos"])


def map_file_to_response(f) -> StoredFileResponse:
    """Converte a entidade StoredFile para o schema público incluindo download_url."""
    return StoredFileResponse(
        id=f.id,
        workspace_id=f.workspace_id,
        uploaded_by_user_id=f.uploaded_by_user_id,
        filename=f.filename,
        content_type=f.content_type,
        file_size_bytes=f.file_size_bytes,
        storage_backend=f.storage_backend,
        is_public=f.is_public,
        download_url=build_download_url(f.id),
        created_at=f.created_at,
    )


@router.post(
    "/workspaces/{workspace_id}/storage/upload",
    response_model=StoredFileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Fazer upload de arquivo no workspace",
    description="Armazena um anexo, relatório ou documento associado ao workspace. Requer permissão mínima de Membro.",
)
async def upload_file(
    workspace_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.MEMBER))] = None,
    session: Annotated[AsyncSession, Depends(get_db)] = None,
    request: Request = None,
) -> StoredFileResponse:
    _ = membership
    content = await file.read()
    stored_file = await upload_workspace_file(
        session=session,
        workspace_id=workspace_id,
        user_id=current_user.id,
        filename=file.filename or "arquivo_anexo",
        content_type=file.content_type or "application/octet-stream",
        data=content,
    )

    await log_audit_event(
        action="file.uploaded",
        resource_type="stored_file",
        resource_id=str(stored_file.id),
        workspace_id=workspace_id,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )

    await trigger_webhook_event(
        session=session,
        workspace_id=workspace_id,
        event_type="file.uploaded",
        payload={
            "file_id": str(stored_file.id),
            "filename": stored_file.filename,
            "file_size_bytes": stored_file.file_size_bytes,
            "content_type": stored_file.content_type,
            "uploaded_by": str(current_user.id),
        },
    )

    return map_file_to_response(stored_file)


@router.get(
    "/workspaces/{workspace_id}/storage/files",
    response_model=StoredFileListResponse,
    summary="Listar arquivos do workspace",
    description="Retorna o catálogo de arquivos anexados ao workspace. Requer permissão mínima de Viewer.",
)
async def list_files(
    workspace_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.VIEWER))] = None,
    session: Annotated[AsyncSession, Depends(get_db)] = None,
) -> StoredFileListResponse:
    _ = membership
    files = await list_workspace_files(session, workspace_id)
    total = await count_workspace_files(session, workspace_id)
    return StoredFileListResponse(
        items=[map_file_to_response(f) for f in files],
        total=total,
    )


@router.delete(
    "/workspaces/{workspace_id}/storage/files/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir arquivo do workspace",
    description="Exclui o arquivo do disco/storage e apaga o registro do banco de dados. Requer permissão de Membro.",
)
async def delete_file(
    workspace_id: uuid.UUID,
    file_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.MEMBER))] = None,
    session: Annotated[AsyncSession, Depends(get_db)] = None,
    request: Request = None,
) -> None:
    _ = membership
    file = await delete_workspace_file(session, workspace_id, file_id)

    await log_audit_event(
        action="file.deleted",
        resource_type="stored_file",
        resource_id=str(file.id),
        workspace_id=workspace_id,
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )

    await trigger_webhook_event(
        session=session,
        workspace_id=workspace_id,
        event_type="file.deleted",
        payload={
            "file_id": str(file.id),
            "filename": file.filename,
            "deleted_by": str(current_user.id),
        },
    )


@router.get(
    "/storage/files/{file_id}/download",
    summary="Baixar ou visualizar arquivo",
    description="Faz streaming do arquivo solicitado. Arquivos públicos (como avatares) não exigem autenticação.",
)
async def download_file(
    file_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user)] = None,
) -> Response:
    file = await get_stored_file(session, file_id)

    # Se não for público, valida autenticação e tenant
    if not file.is_public:
        if not current_user:
            raise ForbiddenException(message="Acesso restrito a membros autorizados.")
        if file.workspace_id:
            membership_stmt = select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == file.workspace_id,
                WorkspaceMember.user_id == current_user.id,
            )
            res = await session.execute(membership_stmt)
            if not res.scalar_one_or_none():
                raise ForbiddenException(message="Você não possui autorização para baixar este arquivo.")

    data = read_bytes(file.storage_path)
    return Response(
        content=data,
        media_type=file.content_type,
        headers={"Content-Disposition": f'inline; filename="{file.filename}"'},
    )


@router.post(
    "/users/me/avatar",
    response_model=AvatarUploadResponse,
    summary="Atualizar avatar do usuário",
    description="Faz upload de uma imagem de perfil, persiste como arquivo público e atualiza o campo avatar_url do usuário.",
)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    session: Annotated[AsyncSession, Depends(get_db)] = None,
    request: Request = None,
) -> AvatarUploadResponse:
    content = await file.read()
    stored_file, avatar_url = await upload_user_avatar(
        session=session,
        user=current_user,
        filename=file.filename or "avatar.png",
        content_type=file.content_type or "image/png",
        data=content,
    )

    await log_audit_event(
        action="user.avatar_updated",
        resource_type="user",
        resource_id=str(current_user.id),
        user_id=current_user.id,
        user_email=current_user.email,
        request=request,
    )

    return AvatarUploadResponse(avatar_url=avatar_url, file_id=stored_file.id)
