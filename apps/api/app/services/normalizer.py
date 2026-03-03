"""Servicio normalizador — convierte la salida cruda de conectores en registros Event."""

import logging
from datetime import datetime, timezone
from typing import Optional

from geoalchemy2.shape import from_shape
from shapely import wkt as shapely_wkt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event, EventSource, EventType, Severity

logger = logging.getLogger(__name__)

# Mapeo Cadena → Enum
SOURCE_MAP = {s.value: s for s in EventSource}
TYPE_MAP = {t.value: t for t in EventType}
SEVERITY_MAP = {s.value: s for s in Severity}


class Normalizer:
    """
    Toma dicts de eventos crudos de los conectores y los inserta/actualiza en la BD.
    Gestiona la deduplicación mediante source_id.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_events(self, raw_events: list[dict]) -> list[Event]:
        """Procesa un lote de dicts de eventos crudos — inserta nuevos, omite duplicados."""
        created = []

        for raw in raw_events:
            try:
                event = await self._upsert_event(raw)
                if event:
                    created.append(event)
            except Exception as e:
                logger.warning("Error al normalizar evento %s: %s", raw.get("source_id", "?"), e)

        if created:
            await self.db.flush()
            logger.info("Normalizador: %d nuevos eventos ingestados", len(created))

        return created

    async def _upsert_event(self, raw: dict) -> Optional[Event]:
        """Inserta un nuevo evento o actualiza si source_id ya existe con cambios."""
        source_id = raw.get("source_id", "")
        if not source_id:
            return None

        # Comprobar evento existente
        result = await self.db.execute(
            select(Event).where(Event.source_id == source_id)
        )
        existing_event = result.scalar_one_or_none()

        if existing_event:
            # Actualizar campos que puedan haber cambiado
            updated = False
            new_severity = SEVERITY_MAP.get(raw.get("severity", ""))
            new_expires = self._parse_datetime(raw.get("expires"))
            new_description = raw.get("description")

            if new_severity and existing_event.severity != new_severity:
                existing_event.severity = new_severity
                updated = True
            if new_expires and existing_event.expires != new_expires:
                existing_event.expires = new_expires
                updated = True
            if new_description and existing_event.description != new_description:
                existing_event.description = new_description
                updated = True

            return existing_event if updated else None

        # Parsear geometría desde WKT
        geometry = None
        area_wkt = raw.get("area_wkt")
        if area_wkt:
            try:
                geom_shape = shapely_wkt.loads(area_wkt)
                geometry = from_shape(geom_shape, srid=4326)
            except Exception as e:
                logger.warning("WKT inválido para %s: %s", source_id, e)

        # Parsear marcas de tiempo
        effective = self._parse_datetime(raw.get("effective"))
        expires = self._parse_datetime(raw.get("expires"))

        # Si no hay hora efectiva, usar ahora
        if not effective:
            effective = datetime.now(timezone.utc)

        # Mapear enums
        source = SOURCE_MAP.get(raw.get("source", ""), EventSource.AEMET)
        event_type = TYPE_MAP.get(raw.get("event_type", ""), EventType.OTHER)
        severity = SEVERITY_MAP.get(raw.get("severity", ""), Severity.GREEN)

        event = Event(
            source=source,
            source_id=source_id,
            event_type=event_type,
            severity=severity,
            title=raw.get("title", "Sin título"),
            description=raw.get("description"),
            instructions=raw.get("instructions"),
            area=geometry,
            area_name=raw.get("area_name"),
            effective=effective,
            expires=expires,
            source_url=raw.get("source_url"),
            magnitude=raw.get("magnitude"),
            depth_km=raw.get("depth_km"),
            raw_data=raw.get("raw_data"),
        )

        self.db.add(event)
        return event

    @staticmethod
    def _parse_datetime(value) -> Optional[datetime]:
        """Intenta parsear un datetime desde varios formatos."""
        if not value:
            return None
        if isinstance(value, datetime):
            return value

        for fmt in [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
        ]:
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue

        # Intentar formato ISO
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

        return None
