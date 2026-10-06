import argparse
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TEMPLATES = {
    "__init__.py": '"""{cap_name} vertical slice."""\n',
    "models.py": '''import uuid
from sqlalchemy import Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base


class {cap_singular}(Base):
    __tablename__ = "{name}"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
''',
    "schemas.py": '''from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, Field


class {cap_singular}Create(BaseModel):
    title: str = Field(min_length=2, max_length=150, description="Título do registro")
    description: str | None = Field(default=None, max_length=1000)


class {cap_singular}Update(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    is_active: bool | None = None


class {cap_singular}Response(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    description: str | None
    is_active: bool
    created_at: datetime
''',
    "service.py": '''import uuid
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.errors import NotFoundException
from src.slices.{name}.models import {cap_singular}
from src.slices.{name}.schemas import {cap_singular}Create, {cap_singular}Update


async def create_{singular}(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    req: {cap_singular}Create,
) -> {cap_singular}:
    item = {cap_singular}(
        workspace_id=workspace_id,
        title=req.title,
        description=req.description,
    )
    session.add(item)
    await session.flush()
    return item


async def list_{name}(
    session: AsyncSession,
    workspace_id: uuid.UUID,
) -> list[{cap_singular}]:
    stmt = (
        select({cap_singular})
        .where({cap_singular}.workspace_id == workspace_id)
        .order_by({cap_singular}.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_{singular}(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    item_id: uuid.UUID,
) -> {cap_singular}:
    stmt = select({cap_singular}).where(
        {cap_singular}.id == item_id,
        {cap_singular}.workspace_id == workspace_id,
    )
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()
    if not item:
        raise NotFoundException(message="{cap_singular} não encontrado")
    return item


async def update_{singular}(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    item_id: uuid.UUID,
    req: {cap_singular}Update,
) -> {cap_singular}:
    item = await get_{singular}(session, workspace_id, item_id)
    if req.title is not None:
        item.title = req.title
    if req.description is not None:
        item.description = req.description
    if req.is_active is not None:
        item.is_active = req.is_active
    await session.flush()
    return item


async def delete_{singular}(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    item_id: uuid.UUID,
) -> None:
    stmt = delete({cap_singular}).where(
        {cap_singular}.id == item_id,
        {cap_singular}.workspace_id == workspace_id,
    )
    result = await session.execute(stmt)
    if result.rowcount == 0:
        raise NotFoundException(message="{cap_singular} não encontrado")
''',
    "router.py": '''from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.slices.{name}.schemas import (
    {cap_singular}Create,
    {cap_singular}Response,
    {cap_singular}Update,
)
from src.slices.{name}.service import (
    create_{singular},
    delete_{singular},
    get_{singular},
    list_{name},
    update_{singular},
)
from src.slices.workspaces.dependencies import require_workspace_role
from src.slices.workspaces.models import WorkspaceMember, WorkspaceRole

router = APIRouter(prefix="/workspaces/{{workspace_id}}/{name}", tags=["{cap_name}"])


@router.post("", response_model={cap_singular}Response, status_code=status.HTTP_201_CREATED)
async def create(
    workspace_id: uuid.UUID,
    req: {cap_singular}Create,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.MEMBER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> {cap_singular}Response:
    _ = membership
    item = await create_{singular}(session, workspace_id, req)
    return {cap_singular}Response.model_validate(item)


@router.get("", response_model=list[{cap_singular}Response])
async def list_all(
    workspace_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.VIEWER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[{cap_singular}Response]:
    _ = membership
    items = await list_{name}(session, workspace_id)
    return [{cap_singular}Response.model_validate(i) for i in items]


@router.get("/{{item_id}}", response_model={cap_singular}Response)
async def get_by_id(
    workspace_id: uuid.UUID,
    item_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.VIEWER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> {cap_singular}Response:
    _ = membership
    item = await get_{singular}(session, workspace_id, item_id)
    return {cap_singular}Response.model_validate(item)


@router.patch("/{{item_id}}", response_model={cap_singular}Response)
async def update(
    workspace_id: uuid.UUID,
    item_id: uuid.UUID,
    req: {cap_singular}Update,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.MEMBER))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> {cap_singular}Response:
    _ = membership
    item = await update_{singular}(session, workspace_id, item_id, req)
    return {cap_singular}Response.model_validate(item)


@router.delete("/{{item_id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    workspace_id: uuid.UUID,
    item_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    _ = membership
    await delete_{singular}(session, workspace_id, item_id)
''',
}


def scaffold_slice(name: str) -> None:
    name = name.lower().strip()
    singular = name[:-1] if name.endswith("s") else name
    cap_name = name.capitalize()
    cap_singular = singular.capitalize()

    root_dir = Path(__file__).resolve().parent.parent.parent
    slice_dir = root_dir / "apps" / "api" / "src" / "slices" / name
    tests_dir = slice_dir / "tests"

    if slice_dir.exists():
        print(f"⚠️ A fatia '{name}' já existe em {slice_dir}")
        return

    os.makedirs(tests_dir, exist_ok=True)

    subs = {
        "name": name,
        "singular": singular,
        "cap_name": cap_name,
        "cap_singular": cap_singular,
    }

    for filename, tmpl in TEMPLATES.items():
        file_path = slice_dir / filename
        content = tmpl.format(**subs)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    # Test file
    test_file = tests_dir / f"test_{name}_slice.py"
    test_content = f'''import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_{name}_slice_lifecycle(client: AsyncClient) -> None:
    # 1. Registrar usuário e obter token
    reg = await client.post(
        "/api/v1/auth/register",
        json={{"email": "{name}@test.com", "password": "Password123!", "full_name": "{cap_name} Tester"}},
    )
    assert reg.status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={{"email": "{name}@test.com", "password": "Password123!"}},
    )
    headers = {{"Authorization": f"Bearer {{login.json()['access_token']}}"}}

    # 2. Criar workspace
    ws_res = await client.post("/api/v1/workspaces", json={{"name": "{cap_name} Org"}}, headers=headers)
    workspace_id = ws_res.json()["id"]

    # 3. Criar registro na fatia {name}
    item_res = await client.post(
        f"/api/v1/workspaces/{{workspace_id}}/{name}",
        json={{"title": "Exemplo Inicial de {cap_singular}"}},
        headers=headers,
    )
    assert item_res.status_code == 201
    item_id = item_res.json()["id"]

    # 4. Listar registros
    list_res = await client.get(f"/api/v1/workspaces/{{workspace_id}}/{name}", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
'''
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_content)

    print(f"✨ Fatia vertical '{name}' criada com sucesso em: {slice_dir}")
    print(f"👉 Para ativar na API, registre o router em apps/api/src/main.py:")
    print(f"   from src.slices.{name}.router import router as {name}_router")
    print(f"   app.include_router({name}_router, prefix=settings.API_V1_STR)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffold de nova fatia vertical no SoftForge")
    parser.add_argument("--name", required=True, help="Nome da fatia no plural (ex: invoices, customers)")
    args = parser.parse_args()
    scaffold_slice(args.name)
