"""Subscriptions API — zone, filter, and user settings management."""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from geoalchemy2.functions import ST_AsGeoJSON
from geoalchemy2.shape import from_shape
from shapely.geometry import shape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserZone, UserFilter
from app.api.deps import get_current_user
from app.schemas import (
    ZoneCreate,
    ZoneOut,
    FilterCreate,
    FilterOut,
    UserSettingsUpdate,
    UserOut,
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


# ── Zones ─────────────────────────────────────────────────────────────────────


@router.get("/zones", response_model=list[ZoneOut])
async def list_zones(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserZone, ST_AsGeoJSON(UserZone.geometry).label("geojson")).where(UserZone.user_id == user.id)
    )
    rows = result.all()
    return [
        ZoneOut(id=r.UserZone.id, label=r.UserZone.label, geojson=json.loads(r.geojson) if r.geojson else None)
        for r in rows
    ]


@router.post("/zones", response_model=ZoneOut, status_code=201)
async def create_zone(
    data: ZoneCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Maximum 4 zones per user (Yurekuru style)
    count_result = await db.execute(select(UserZone).where(UserZone.user_id == user.id))
    if len(count_result.all()) >= 4:
        raise HTTPException(status_code=400, detail="Máximo 4 zonas permitidas")

    # Convert GeoJSON to PostGIS geometry
    geom = from_shape(shape(data.geojson), srid=4326)

    zone = UserZone(user_id=user.id, label=data.label, geometry=geom)
    db.add(zone)
    await db.flush()

    return ZoneOut(id=zone.id, label=zone.label, geojson=data.geojson)


@router.delete("/zones/{zone_id}", status_code=204)
async def delete_zone(
    zone_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserZone).where(UserZone.id == zone_id, UserZone.user_id == user.id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zona no encontrada")
    await db.delete(zone)


# ── Filters ─────────────────────────────────────────────────────────────────────────


@router.get("/filters", response_model=list[FilterOut])
async def list_filters(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserFilter).where(UserFilter.user_id == user.id))
    return [FilterOut.model_validate(f) for f in result.scalars().all()]


@router.post("/filters", response_model=FilterOut, status_code=201)
async def create_filter(
    data: FilterCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filt = UserFilter(
        user_id=user.id,
        event_types=data.event_types,
        min_severity=data.min_severity,
    )
    db.add(filt)
    await db.flush()
    return FilterOut.model_validate(filt)


@router.delete("/filters/{filter_id}", status_code=204)
async def delete_filter(
    filter_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserFilter).where(UserFilter.id == filter_id, UserFilter.user_id == user.id))
    filt = result.scalar_one_or_none()
    if not filt:
        raise HTTPException(status_code=404, detail="Filtro no encontrado")
    await db.delete(filt)


# ── User Settings ───────────────────────────────────────────────────────────────


@router.patch("/settings", response_model=UserOut)
async def update_settings(
    data: UserSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.quiet_start is not None:
        user.quiet_start = data.quiet_start
    if data.quiet_end is not None:
        user.quiet_end = data.quiet_end
    if data.predictive_alerts is not None:
        user.predictive_alerts = data.predictive_alerts
    if data.fcm_token is not None:
        user.fcm_token = data.fcm_token
    await db.flush()
    return UserOut.model_validate(user)
