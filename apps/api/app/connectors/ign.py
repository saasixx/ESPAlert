"""Conector IGN de Terremotos — obtiene datos sísmicos de servicios web FDSN."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Portal Sísmico EMSC - servicio de eventos FDSN (incluye datos IGN/CSN)
FDSN_BASE = "https://seismicportal.eu/fdsnws/event/1"

# Página web del IGN para últimos terremotos (scrape fallback)
IGN_LATEST_URL = "https://www.ign.es/web/ign/portal/ultimos-terremotos/-/ultimos-terremotos/getUltimosTerremotos"

# Mapeo Magnitud → Severidad
MAGNITUDE_SEVERITY = [
    (5.0, "red"),
    (4.0, "orange"),
    (3.0, "yellow"),
    (0.0, "green"),
]


def magnitude_to_severity(mag: float) -> str:
    for threshold, severity in MAGNITUDE_SEVERITY:
        if mag >= threshold:
            return severity
    return "green"


class IGNConnector:
    """
    Obtiene datos de terremotos de los servicios web FDSN del IGN.

    Primario: consulta de eventos FDSN (text/csv o formatos JSON)
    Fallback: endpoint web de últimos terremotos del IGN
    """

    async def fetch_earthquakes(self, hours_back: int = 24) -> list[dict]:
        """Obtiene terremotos recientes del servicio FDSN."""
        events = []

        try:
            events = await self._fetch_fdsn(hours_back)
        except Exception as e:
            logger.warning("FDSN falló, intentando fallback: %s", e)
            try:
                events = await self._fetch_latest_fallback()
            except Exception as e2:
                logger.exception("Fallback IGN también falló: %s", e2)

        logger.info("IGN: obtenidos %d terremotos", len(events))
        return events

    async def _fetch_fdsn(self, hours_back: int) -> list[dict]:
        """Obtiene datos del servicio web de eventos FDSN (formato texto)."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours_back)

        params = {
            "starttime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "endtime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "minlatitude": 25.0,   # Sur de Canarias
            "maxlatitude": 45.0,   # Norte de España
            "minlongitude": -20.0, # Oeste de Canarias
            "maxlongitude": 6.0,   # Costa mediterránea oriental
            "format": "text",
            "orderby": "time",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{FDSN_BASE}/query", params=params)

            if resp.status_code == 204:
                # Sin contenido = no hay terremotos en la ventana temporal
                return []

            if resp.status_code != 200:
                raise Exception(f"FDSN returned {resp.status_code}: {resp.text[:200]}")

            return self._parse_fdsn_text(resp.text)

    def _parse_fdsn_text(self, text: str) -> list[dict]:
        """
        Parsea formato texto FDSN:
        EventID|Time|Latitude|Longitude|Depth/km|Author|Catalog|Contributor|ContributorID|MagType|Magnitude|MagAuthor|EventLocationName
        """
        events = []
        lines = text.strip().split("\n")

        for line in lines[1:]:  # Saltar cabecera
            parts = line.split("|")
            if len(parts) < 13:
                continue

            try:
                event_id = parts[0].strip()
                time_str = parts[1].strip()
                lat = float(parts[2].strip())
                lon = float(parts[3].strip())
                depth = parts[4].strip()
                mag_type = parts[9].strip()
                magnitude = float(parts[10].strip()) if parts[10].strip() else 0.0
                location_name = parts[12].strip() if len(parts) > 12 else ""

                # Parsear fecha y hora
                try:
                    event_time = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                except ValueError:
                    event_time = datetime.now(timezone.utc)

                severity = magnitude_to_severity(magnitude)

                events.append({
                    "source": "ign",
                    "source_id": f"ign-{event_id}",
                    "event_type": "earthquake",
                    "severity": severity,
                    "title": f"Terremoto M{magnitude} — {location_name}",
                    "description": (
                        f"Magnitud: {magnitude} ({mag_type})\n"
                        f"Profundidad: {depth} km\n"
                        f"Ubicación: {location_name}\n"
                        f"Coordenadas: {lat}°N, {lon}°{'W' if lon < 0 else 'E'}"
                    ),
                    "instructions": self._get_earthquake_instructions(magnitude),
                    "area_wkt": f"POINT({lon} {lat})",
                    "area_name": location_name,
                    "effective": event_time.isoformat(),
                    "expires": (event_time + timedelta(hours=24)).isoformat(),
                    "source_url": f"https://www.ign.es/web/ign/portal/sis-catalogo-terremotos",
                    "magnitude": str(magnitude),
                    "depth_km": str(depth),
                    "raw_data": {
                        "event_id": event_id,
                        "lat": lat,
                        "lon": lon,
                        "depth_km": depth,
                        "magnitude": magnitude,
                        "mag_type": mag_type,
                        "location": location_name,
                    },
                })
            except (ValueError, IndexError) as e:
                logger.warning("Error al parsear línea FDSN: %s", e)

        return events

    async def _fetch_latest_fallback(self) -> list[dict]:
        """Fallback: obtiene datos del endpoint web de últimos terremotos del IGN."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(IGN_LATEST_URL)
            if resp.status_code != 200:
                raise Exception(f"IGN latest endpoint returned {resp.status_code}")

            data = resp.json()
            events = []

            for quake in data if isinstance(data, list) else []:
                try:
                    mag = float(quake.get("mag", 0))
                    lat = float(quake.get("lat", 0))
                    lon = float(quake.get("lon", 0))
                    depth = quake.get("depth", "")
                    location = quake.get("localizacion", "")
                    event_id = quake.get("evid", "")
                    time_str = quake.get("fecha", "")

                    events.append({
                        "source": "ign",
                        "source_id": f"ign-{event_id}",
                        "event_type": "earthquake",
                        "severity": magnitude_to_severity(mag),
                        "title": f"Terremoto M{mag} — {location}",
                        "description": f"Magnitud: {mag}\nProfundidad: {depth} km\nUbicación: {location}",
                        "instructions": self._get_earthquake_instructions(mag),
                        "area_wkt": f"POINT({lon} {lat})",
                        "area_name": location,
                        "effective": time_str,
                        "expires": "",
                        "source_url": "https://www.ign.es/web/ign/portal/sis-catalogo-terremotos",
                        "magnitude": str(mag),
                        "depth_km": str(depth),
                        "raw_data": quake,
                    })
                except (ValueError, KeyError) as e:
                    logger.warning("Error al parsear terremoto fallback IGN: %s", e)

            return events

    @staticmethod
    def _get_earthquake_instructions(magnitude: float) -> str:
        if magnitude >= 5.0:
            return (
                "🔴 TERREMOTO SIGNIFICATIVO\n"
                "• Aléjese de ventanas y objetos que puedan caer\n"
                "• Si está en interior: cúbrase bajo una mesa resistente\n"
                "• Si está en exterior: aléjese de edificios y tendidos eléctricos\n"
                "• Después: compruebe daños estructurales antes de entrar a edificios\n"
                "• Esté atento a réplicas"
            )
        elif magnitude >= 4.0:
            return (
                "🟠 TERREMOTO MODERADO\n"
                "• Puede sentirse con claridad\n"
                "• Mantenga la calma\n"
                "• Aléjese de estanterías y objetos pesados en altura\n"
                "• Si está cerca de la costa, esté atento a avisos de tsunami"
            )
        elif magnitude >= 3.0:
            return (
                "🟡 TERREMOTO LEVE\n"
                "• Puede sentirse en interiores\n"
                "• No suele causar daños\n"
                "• Manténgase informado por si hay réplicas"
            )
        else:
            return "🟢 Terremoto de baja magnitud. No se esperan daños."
