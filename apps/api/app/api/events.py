"""API de Eventos — listado, filtrado y consulta de alertas."""

import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID, ST_AsGeoJSON
from sqlalchemy import select, and_, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import Event
from app.schemas import EventOut, EventListParams

router = APIRouter(prefix="/events", tags=["events"])


def _event_to_out(event: Event, area_geojson: str | None = None) -> EventOut:
    """Convierte un Event de SQLAlchemy a un EventOut de Pydantic."""
    return EventOut(
        id=event.id,
        source=event.source.value if event.source else "",
        source_id=event.source_id,
        event_type=event.event_type.value if event.event_type else "",
        severity=event.severity.value if event.severity else "",
        title=event.title,
        description=event.description,
        instructions=event.instructions,
        area_name=event.area_name,
        area_geojson=json.loads(area_geojson) if area_geojson else None,
        effective=event.effective,
        expires=event.expires,
        source_url=event.source_url,
        magnitude=event.magnitude,
        depth_km=event.depth_km,
        created_at=event.created_at,
    )


@router.get("/", response_model=list[EventOut])
async def list_events(
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    active_only: bool = Query(True),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    radius_km: float = Query(50.0),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """Lista eventos de alerta con filtros opcionales (tipo, severidad, geo-radio)."""
    now = datetime.now(timezone.utc)

    stmt = select(Event, ST_AsGeoJSON(Event.area).label("area_geojson"))

    conditions = []

    if active_only:
        conditions.append(
            and_(
                Event.effective <= now,
                Event.expires >= now,
            )
        )

    if event_type:
        conditions.append(Event.event_type == event_type)

    if severity:
        conditions.append(Event.severity == severity)

    if source:
        conditions.append(Event.source == source)

    # Filtro de geo-radio (punto + distancia)
    if lat is not None and lon is not None:
        point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)
        # ST_DWithin con cast a geografía para metros
        conditions.append(
            ST_DWithin(
                sa_func.cast(Event.area, sa_func.Geography),
                sa_func.cast(point, sa_func.Geography),
                radius_km * 1000,  # Convertir km a metros
            )
        )

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(Event.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    rows = result.all()

    return [_event_to_out(row.Event, row.area_geojson) for row in rows]


@router.get("/{event_id}", response_model=EventOut)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene un evento por su ID con geometría completa."""
    stmt = select(Event, ST_AsGeoJSON(Event.area).label("area_geojson")).where(
        Event.id == event_id
    )
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    return _event_to_out(row.Event, row.area_geojson)


@router.get("/active/summary")
async def active_summary(db: AsyncSession = Depends(get_db)):
    """Resumen rápido de eventos activos agrupados por tipo y severidad."""
    now = datetime.now(timezone.utc)

    stmt = (
        select(
            Event.event_type,
            Event.severity,
            sa_func.count(Event.id).label("count"),
        )
        .where(and_(Event.effective <= now, Event.expires >= now))
        .group_by(Event.event_type, Event.severity)
    )
    result = await db.execute(stmt)
    rows = result.all()

    summary = {}
    for row in rows:
        etype = row.event_type.value if row.event_type else "unknown"
        if etype not in summary:
            summary[etype] = {}
        summary[etype][row.severity.value if row.severity else "unknown"] = row.count

    return {"active_events": summary, "timestamp": now.isoformat()}
