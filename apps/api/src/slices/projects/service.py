import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundException
from src.slices.projects.models import Project, Task
from src.slices.projects.schemas import (
    PaginatedProjectsResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    TaskCreate,
    TaskResponse,
)


async def create_project(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    req: ProjectCreate,
) -> ProjectResponse:
    project = Project(
        workspace_id=workspace_id,
        name=req.name,
        description=req.description,
        created_by_id=user_id,
        is_archived=False,
    )
    session.add(project)
    await session.flush()

    return ProjectResponse(
        id=project.id,
        workspace_id=project.workspace_id,
        name=project.name,
        description=project.description,
        is_archived=project.is_archived,
        created_at=project.created_at,
        tasks_count=0,
    )


async def list_projects(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    search: str | None = None,
    include_archived: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> PaginatedProjectsResponse:
    # Contagem total
    count_stmt = select(func.count(Project.id)).where(Project.workspace_id == workspace_id)
    if not include_archived:
        count_stmt = count_stmt.where(Project.is_archived.is_(False))
    if search:
        count_stmt = count_stmt.where(Project.name.ilike(f"%{search}%"))

    total_res = await session.execute(count_stmt)
    total = total_res.scalar_one()

    # Query com contagem de tarefas vinculadas
    tasks_count_subq = (
        select(func.count(Task.id)).where(Task.project_id == Project.id).scalar_subquery()
    )

    query_stmt = select(Project, tasks_count_subq.label("tasks_count")).where(
        Project.workspace_id == workspace_id
    )
    if not include_archived:
        query_stmt = query_stmt.where(Project.is_archived.is_(False))
    if search:
        query_stmt = query_stmt.where(Project.name.ilike(f"%{search}%"))

    query_stmt = query_stmt.order_by(Project.created_at.desc()).limit(limit).offset(offset)
    results = await session.execute(query_stmt)

    items = []
    for proj, t_count in results.all():
        items.append(
            ProjectResponse(
                id=proj.id,
                workspace_id=proj.workspace_id,
                name=proj.name,
                description=proj.description,
                is_archived=proj.is_archived,
                created_at=proj.created_at,
                tasks_count=t_count or 0,
            )
        )

    return PaginatedProjectsResponse(items=items, total=total, limit=limit, offset=offset)


async def get_project(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
) -> ProjectResponse:
    tasks_count_subq = (
        select(func.count(Task.id)).where(Task.project_id == Project.id).scalar_subquery()
    )
    stmt = select(Project, tasks_count_subq.label("tasks_count")).where(
        Project.id == project_id, Project.workspace_id == workspace_id
    )
    result = await session.execute(stmt)
    row = result.first()
    if not row:
        raise NotFoundException(message="Projeto não encontrado neste workspace")

    proj, t_count = row
    return ProjectResponse(
        id=proj.id,
        workspace_id=proj.workspace_id,
        name=proj.name,
        description=proj.description,
        is_archived=proj.is_archived,
        created_at=proj.created_at,
        tasks_count=t_count or 0,
    )


async def update_project(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
    req: ProjectUpdate,
) -> ProjectResponse:
    stmt = select(Project).where(Project.id == project_id, Project.workspace_id == workspace_id)
    result = await session.execute(stmt)
    proj = result.scalar_one_or_none()
    if not proj:
        raise NotFoundException(message="Projeto não encontrado")

    if req.name is not None:
        proj.name = req.name
    if req.description is not None:
        proj.description = req.description
    if req.is_archived is not None:
        proj.is_archived = req.is_archived

    await session.flush()
    return await get_project(session, workspace_id, project_id)


async def delete_project(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    project_id: uuid.UUID,
) -> None:
    stmt = delete(Project).where(Project.id == project_id, Project.workspace_id == workspace_id)
    result = await session.execute(stmt)
    if result.rowcount == 0:
        raise NotFoundException(message="Projeto não encontrado")


async def create_task(
    session: AsyncSession,
    project_id: uuid.UUID,
    req: TaskCreate,
) -> TaskResponse:
    task = Task(
        project_id=project_id,
        title=req.title,
        status=req.status,
        priority=req.priority,
        due_date=req.due_date,
        assigned_to_id=req.assigned_to_id,
    )
    session.add(task)
    await session.flush()
    return TaskResponse.model_validate(task)


async def list_project_tasks(
    session: AsyncSession,
    project_id: uuid.UUID,
) -> list[TaskResponse]:
    stmt = select(Task).where(Task.project_id == project_id).order_by(Task.created_at.asc())
    results = await session.execute(stmt)
    return [TaskResponse.model_validate(t) for t in results.scalars().all()]
