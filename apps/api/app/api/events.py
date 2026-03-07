"""Events API — listing, filtering, and alert querying."""

import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID, ST_AsGeoJSON
from sqlalchemy import select, and_, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, get_redis
from app.models.event import Event
from app.schemas import EventOut
from app.services.cache import (
    events_cache_key,
    get_cached,
    set_cached,
    CACHE_TTL_EVENTS,
    CACHE_TTL_SUMMARY,
    KEY_SUMMARY,
)

router = APIRouter(prefix="/events", tags=["events"])


def _event_to_out(event: Event, area_geojson: str | None = None) -> EventOut:
    """Convert a SQLAlchemy Event to a Pydantic EventOut."""
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
    """List alert events with optional filters (type, severity, geo-radius)."""
    redis = get_redis()
    cache_key = events_cache_key({
        "event_type": event_type,
        "severity": severity,
        "source": source,
        "active_only": active_only,
        "lat": lat,
        "lon": lon,
        "radius_km": radius_km,
        "limit": limit,
        "offset": offset,
    })

    cached = await get_cached(redis, cache_key)
    if cached is not None:
        return cached

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

    if lat is not None and lon is not None:
        point = ST_SetSRID(ST_MakePoint(lon, lat), 4326)
        conditions.append(
            ST_DWithin(
                sa_func.cast(Event.area, sa_func.Geography),
                sa_func.cast(point, sa_func.Geography),
                radius_km * 1000,
            )
        )

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(Event.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    rows = result.all()

    events_out = [_event_to_out(row.Event, row.area_geojson) for row in rows]

    # Store serialized form (list of dicts) in cache
    serializable = [e.model_dump(mode="json") for e in events_out]
    await set_cached(redis, cache_key, serializable, CACHE_TTL_EVENTS)

    return events_out


@router.get("/{event_id}", response_model=EventOut)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get an event by its ID with full geometry."""
    stmt = select(Event, ST_AsGeoJSON(Event.area).label("area_geojson")).where(Event.id == event_id)
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Event not found")

    return _event_to_out(row.Event, row.area_geojson)


@router.get("/active/summary")
async def active_summary(db: AsyncSession = Depends(get_db)):
    """Quick summary of active events grouped by type and severity."""
    redis = get_redis()

    cached = await get_cached(redis, KEY_SUMMARY)
    if cached is not None:
        return cached

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

    summary: dict = {}
    for row in rows:
        etype = row.event_type.value if row.event_type else "unknown"
        if etype not in summary:
            summary[etype] = {}
        summary[etype][row.severity.value if row.severity else "unknown"] = row.count

    payload = {"active_events": summary, "timestamp": now.isoformat()}
    await set_cached(redis, KEY_SUMMARY, payload, CACHE_TTL_SUMMARY)

    return payload
