"""AEMET OpenData connector — fetches weather warnings (CAP format)."""

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
import xmltodict

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

AEMET_BASE = "https://opendata.aemet.es/opendata/api"

# AEMET area codes for Spain (peninsula + islands + Ceuta/Melilla)
AEMET_AREAS = [
    "61",  # España peninsular y Baleares
    "62",  # Canarias
    "63",  # Ceuta
    "64",  # Melilla
]

# Map AEMET severity codes to our severity levels
AEMET_SEVERITY_MAP = {
    "Extreme": "red",
    "Severe": "orange",
    "Moderate": "yellow",
    "Minor": "green",
    "Unknown": "green",
}

# Map AEMET event codes to our event types
AEMET_EVENT_MAP = {
    "Wind": "wind",
    "Viento": "wind",
    "Rain": "rain",
    "Lluvia": "rain",
    "Precipitation": "rain",
    "Precipitación": "rain",
    "Snow": "snow",
    "Nieve": "snow",
    "Ice": "ice",
    "Hielo": "ice",
    "Thunderstorm": "storm",
    "Tormenta": "storm",
    "Fog": "fog",
    "Niebla": "fog",
    "High temperature": "heat",
    "Temperatura máxima": "heat",
    "Low temperature": "cold",
    "Temperatura mínima": "cold",
    "Coastal event": "coastal",
    "Costero": "coastal",
    "Forest fire": "fire_risk",
    "Incendio forestal": "fire_risk",
    "Avalanche": "snow",
    "Alud": "snow",
    "Flooding": "rain",
    "Inundación": "rain",
    "Wave": "wave",
    "Oleaje": "wave",
}


class AemetConnector:
    """
    Fetches weather warnings from AEMET OpenData.

    AEMET uses a two-step fetch pattern:
    1. Request metadata endpoint → get a temporary data URL
    2. Fetch the actual data from the temporary URL
    """

    def __init__(self):
        self.api_key = settings.AEMET_API_KEY
        self.headers = {"api_key": self.api_key}

    async def _fetch_data_url(self, endpoint: str) -> Optional[str]:
        """Step 1: Get the temporary data URL from AEMET."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{AEMET_BASE}/{endpoint}",
                headers=self.headers,
            )
            if resp.status_code != 200:
                logger.error(f"AEMET metadata request failed: {resp.status_code} — {resp.text}")
                return None

            data = resp.json()
            return data.get("datos")

    async def _fetch_data(self, data_url: str) -> Optional[str]:
        """Step 2: Fetch actual data from the temporary URL."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(data_url)
            if resp.status_code != 200:
                logger.error(f"AEMET data fetch failed: {resp.status_code}")
                return None
            return resp.text

    async def fetch_warnings(self) -> list[dict]:
        """
        Fetch all active weather warnings across Spain.
        Returns a list of normalized event dicts ready for the normalizer.
        """
        all_warnings = []

        for area_code in AEMET_AREAS:
            try:
                data_url = await self._fetch_data_url(
                    f"avisos_cap/ultimoelaborado/area/{area_code}"
                )
                if not data_url:
                    continue

                raw_xml = await self._fetch_data(data_url)
                if not raw_xml:
                    continue

                warnings = self._parse_cap_xml(raw_xml, area_code)
                all_warnings.extend(warnings)

            except Exception as e:
                logger.exception(f"Error fetching AEMET area {area_code}: {e}")

        logger.info(f"AEMET: fetched {len(all_warnings)} warnings")
        return all_warnings

    def _parse_cap_xml(self, xml_text: str, area_code: str) -> list[dict]:
        """Parse CAP XML into normalized event dicts."""
        events = []

        try:
            parsed = xmltodict.parse(xml_text)
        except Exception as e:
            logger.error(f"Failed to parse AEMET CAP XML: {e}")
            return events

        # CAP can have single or multiple alerts
        alerts = parsed.get("alert", parsed)
        if isinstance(alerts, dict):
            alerts = [alerts]

        for alert in alerts:
            try:
                info_list = alert.get("info", [])
                if isinstance(info_list, dict):
                    info_list = [info_list]

                for info in info_list:
                    event = self._normalize_cap_info(alert, info, area_code)
                    if event:
                        events.append(event)

            except Exception as e:
                logger.warning(f"Error parsing CAP alert: {e}")

        return events

    def _normalize_cap_info(self, alert: dict, info: dict, area_code: str) -> Optional[dict]:
        """Convert a single CAP <info> block to our event dict."""
        identifier = alert.get("identifier", "")
        event_name = info.get("event", "")
        severity_str = info.get("severity", "Unknown")
        description = info.get("description", "")
        instruction = info.get("instruction", "")
        effective = info.get("effective", "")
        expires = info.get("expires", "")
        headline = info.get("headline", event_name)

        # Parse area / polygon
        area_info = info.get("area", {})
        if isinstance(area_info, list):
            area_info = area_info[0] if area_info else {}

        polygon_str = area_info.get("polygon", "")
        area_desc = area_info.get("areaDesc", "")

        # Convert "lat,lon lat,lon ..." polygon to WKT
        wkt_polygon = self._cap_polygon_to_wkt(polygon_str) if polygon_str else None

        # Map event type
        event_type = "other"
        for key, value in AEMET_EVENT_MAP.items():
            if key.lower() in event_name.lower():
                event_type = value
                break

        return {
            "source": "aemet",
            "source_id": f"aemet-{identifier}-{area_code}",
            "event_type": event_type,
            "severity": AEMET_SEVERITY_MAP.get(severity_str, "green"),
            "title": headline,
            "description": description,
            "instructions": instruction,
            "area_wkt": wkt_polygon,
            "area_name": area_desc,
            "effective": effective,
            "expires": expires,
            "source_url": f"https://www.aemet.es/es/eltiempo/prediccion/avisos",
            "raw_data": {"alert": alert, "info": info},
        }

    @staticmethod
    def _cap_polygon_to_wkt(polygon_str: str) -> Optional[str]:
        """
        Convert CAP polygon string "lat,lon lat,lon ..." to WKT POLYGON.
        CAP uses lat,lon — WKT uses lon lat.
        """
        if not polygon_str or not polygon_str.strip():
            return None

        coords = []
        for pair in polygon_str.strip().split():
            parts = pair.split(",")
            if len(parts) == 2:
                lat, lon = float(parts[0]), float(parts[1])
                coords.append(f"{lon} {lat}")

        if len(coords) < 3:
            return None

        # Close the polygon if needed
        if coords[0] != coords[-1]:
            coords.append(coords[0])

        return f"POLYGON(({', '.join(coords)}))"

    async def fetch_municipal_prediction(self, municipio_code: str) -> Optional[dict]:
        """Fetch hourly prediction for a municipality (for detail screens)."""
        data_url = await self._fetch_data_url(
            f"prediccion/especifica/municipio/horaria/{municipio_code}"
        )
        if not data_url:
            return None

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(data_url)
            if resp.status_code == 200:
                return resp.json()
        return None
