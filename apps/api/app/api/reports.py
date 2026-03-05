"""Collaborative Reports API — crowdsourced 'I felt it' data."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.report import CollaborativeReport
from app.models.user import User
from app.schemas import ReportCreate, ReportOut

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/", status_code=201, response_model=ReportOut)
async def create_report(
    body: ReportCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a collaborative report (authenticated users only)."""
    point = from_shape(Point(body.lon, body.lat), srid=4326)

    report = CollaborativeReport(
        user_id=user.id,
        event_id=body.event_id,
        report_type=body.report_type,
        intensity=body.intensity,
        location=point,
        comment=body.comment,
    )

    db.add(report)
    await db.flush()

    return ReportOut(
        id=report.id,
        report_type=report.report_type,
        intensity=report.intensity,
        lat=body.lat,
        lon=body.lon,
        comment=report.comment,
        event_id=report.event_id,
        created_at=report.created_at,
    )


@router.get("/")
async def list_reports(
    event_id: UUID | None = None,
    report_type: str | None = None,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List recent collaborative reports (public, read-only)."""
    query = select(CollaborativeReport).order_by(CollaborativeReport.created_at.desc())

    if event_id:
        query = query.where(CollaborativeReport.event_id == event_id)
    if report_type:
        query = query.where(CollaborativeReport.report_type == report_type)

    query = query.limit(limit)
    result = await db.execute(query)
    reports = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "report_type": r.report_type,
            "intensity": r.intensity,
            "comment": r.comment,
            "event_id": str(r.event_id) if r.event_id else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in reports
    ]
