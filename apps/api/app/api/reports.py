"""API endpoints for collaborative reports — crowd-sourced 'I feel it' data."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.report import CollaborativeReport

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportCreate(BaseModel):
    report_type: str = Field(..., max_length=50, pattern=r"^(rain|wind|hail|smoke|shaking|flood|fire|other)$")
    intensity: str = Field(..., max_length=20, pattern=r"^(none|light|moderate|strong|extreme)$")
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    comment: str | None = Field(None, max_length=500)
    event_id: UUID | None = None


class ReportResponse(BaseModel):
    id: str
    report_type: str
    intensity: str
    lat: float
    lon: float
    comment: str | None
    event_id: str | None
    created_at: str


@router.post("/", status_code=201, response_model=ReportResponse)
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
    await db.commit()
    await db.refresh(report)

    return ReportResponse(
        id=str(report.id),
        report_type=report.report_type,
        intensity=report.intensity,
        lat=body.lat,
        lon=body.lon,
        comment=report.comment,
        event_id=str(report.event_id) if report.event_id else None,
        created_at=report.created_at.isoformat(),
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
