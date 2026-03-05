"""AEMET OpenData connector — fetches weather warnings (CAP format)."""

import io
import logging
import tarfile
from typing import Optional

import httpx
import xmltodict

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

AEMET_BASE = "https://opendata.aemet.es/opendata/api"

# AEMET area codes for Spain (mainland + islands + Ceuta/Melilla)
AEMET_AREAS = [
    "61",  # Mainland Spain and Balearic Islands
    "62",  # Canary Islands
    "63",  # Ceuta
    "64",  # Melilla
]

# AEMET severity codes to our severity levels
AEMET_SEVERITY_MAP = {
    "Extreme": "red",
    "Severe": "orange",
    "Moderate": "yellow",
    "Minor": "green",
    "Unknown": "green",
}

# AEMET event codes to our event types
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
    Fetch weather warnings from AEMET OpenData.

    AEMET uses a two-step fetch pattern:
    1. Request metadata endpoint → get temporary data URL
    2. Fetch actual data from the temporary URL
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
                logger.error("AEMET metadata request failed: %s — %s", resp.status_code, resp.text)
                return None

            data = resp.json()
            return data.get("datos")

    async def _fetch_data(self, data_url: str) -> Optional[bytes]:
        """Step 2: Fetch actual data from the temporary URL (may be XML or tar)."""
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(data_url)
            if resp.status_code != 200:
                logger.error("AEMET data download failed: %s", resp.status_code)
                return None
            return resp.content

    async def fetch_warnings(self) -> list[dict]:
        """
        Fetch all active weather warnings in Spain.

        AEMET returns a tar file with multiple individual CAP XMLs
        (one per warning). We extract each XML and parse it separately.
        """
        all_warnings = []

        for area_code in AEMET_AREAS:
            try:
                data_url = await self._fetch_data_url(
                    f"avisos_cap/ultimoelaborado/area/{area_code}"
                )
                if not data_url:
                    continue

                raw_data = await self._fetch_data(data_url)
                if not raw_data:
                    continue

                xml_texts = self._extract_cap_xmls(raw_data)
                for xml_text in xml_texts:
                    warnings = self._parse_cap_xml(xml_text, area_code)
                    all_warnings.extend(warnings)

            except Exception as e:
                logger.exception("Error fetching AEMET area %s: %s", area_code, e)

        logger.info("AEMET: fetched %d warnings", len(all_warnings))
        return all_warnings

    @staticmethod
    def _extract_cap_xmls(raw_data: bytes) -> list[str]:
        """
        Extract CAP XMLs from downloaded content.

        AEMET may return a tar with multiple XMLs or a single XML.
        """
        # Try as tar first
        try:
            buf = io.BytesIO(raw_data)
            if tarfile.is_tarfile(buf):
                buf.seek(0)
                xmls = []
                with tarfile.open(fileobj=buf, mode="r:*") as tf:
                    for member in tf.getmembers():
                        if member.isfile() and member.name.endswith(".xml"):
                            f = tf.extractfile(member)
                            if f:
                                xmls.append(f.read().decode("utf-8", errors="replace"))
                if xmls:
                    return xmls
        except (tarfile.TarError, Exception):
            pass

        # If not tar, try as direct XML
        try:
            text = raw_data.decode("utf-8", errors="replace")
            if text.strip().startswith("<?xml") or text.strip().startswith("<alert"):
                return [text]
        except Exception:
            pass

        logger.warning("AEMET: datos no reconocidos como tar ni XML (%d bytes)", len(raw_data))
        return []

    def _parse_cap_xml(self, xml_text: str, area_code: str) -> list[dict]:
        """Parse CAP XML into normalized event dicts."""
        events = []

        try:
            parsed = xmltodict.parse(xml_text)
        except Exception as e:
            logger.error("Error parsing AEMET CAP XML: %s", e)
            return events

        # CAP can have one or multiple alerts
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
                logger.warning("Error parsing CAP alert: %s", e)

        return events

    def _normalize_cap_info(self, alert: dict, info: dict, area_code: str) -> Optional[dict]:
        """Convert a CAP <info> block to our event dict."""
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

        # Convert polygon "lat,lon lat,lon ..." to WKT
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
            "source_url": "https://www.aemet.es/es/eltiempo/prediccion/avisos",
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

        # Close polygon if needed
        if coords[0] != coords[-1]:
            coords.append(coords[0])

        return f"POLYGON(({', '.join(coords)}))"

    async def fetch_municipal_prediction(self, municipio_code: str) -> Optional[dict]:
        """Get hourly prediction for a municipality (for detail screens)."""
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
