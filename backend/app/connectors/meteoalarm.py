"""MeteoAlarm EDR connector — fetches European weather warnings via OGC EDR API."""

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# MeteoAlarm EDR API (public, no key required, CC BY 4.0 license)
EDR_BASE = "https://api.meteoalarm.org/edr/v1"

# MeteoAlarm awareness levels → our severity
AWARENESS_SEVERITY = {
    "1": "green",    # Green — no particular awareness required
    "2": "yellow",   # Yellow — weather is potentially dangerous
    "3": "orange",   # Orange — weather is dangerous
    "4": "red",      # Red — weather is very dangerous
}

# MeteoAlarm awareness types → our event types
AWARENESS_TYPE_MAP = {
    "1": "wind",
    "2": "snow",      # Snow/Ice
    "3": "storm",     # Thunderstorms
    "4": "fog",
    "5": "heat",      # Extreme high temperature
    "6": "cold",      # Extreme low temperature
    "7": "coastal",   # Coastal event
    "8": "fire_risk", # Forest fire
    "9": "wave",      # Avalanche (reuse wave/snow)
    "10": "rain",     # Rain
    "11": "rain",     # Flooding (rain-related)
    "12": "rain",     # Rain-Flood
    "13": "other",    # Unknown
}


class MeteoAlarmConnector:
    """
    Fetches weather warnings from MeteoAlarm's OGC Environmental Data Retrieval API.

    Returns GeoJSON features with warning details for Spain (country code: ES).
    Supplements AEMET data with the standardized European format.
    """

    async def fetch_warnings(self) -> list[dict]:
        """Fetch all active MeteoAlarm warnings for Spain."""
        events = []

        try:
            geojson = await self._query_edr()
            if geojson:
                events = self._parse_geojson(geojson)
        except Exception as e:
            logger.exception(f"Error fetching MeteoAlarm warnings: {e}")

        logger.info(f"MeteoAlarm: fetched {len(events)} warnings")
        return events

    async def _query_edr(self) -> Optional[dict]:
        """Query the EDR API for Spain warnings."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Query active warnings for Spain
            resp = await client.get(
                f"{EDR_BASE}/collections/warnings/items",
                params={
                    "country": "ES",
                    "f": "GeoJSON",
                },
                headers={"Accept": "application/geo+json"},
            )

            if resp.status_code != 200:
                logger.error(f"MeteoAlarm EDR returned {resp.status_code}: {resp.text[:200]}")
                return None

            return resp.json()

    def _parse_geojson(self, geojson: dict) -> list[dict]:
        """Parse MeteoAlarm GeoJSON features into our event format."""
        events = []

        features = geojson.get("features", [])

        for feature in features:
            try:
                event = self._parse_feature(feature)
                if event:
                    events.append(event)
            except Exception as e:
                logger.warning(f"Error parsing MeteoAlarm feature: {e}")

        return events

    def _parse_feature(self, feature: dict) -> Optional[dict]:
        """Parse a single GeoJSON feature into our event dict."""
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        # Extract awareness info
        awareness_level = str(props.get("awareness_level", "1"))
        awareness_type = str(props.get("awareness_type", "13"))

        severity = AWARENESS_SEVERITY.get(awareness_level.split(".")[0] if "." in awareness_level else awareness_level, "green")
        event_type = AWARENESS_TYPE_MAP.get(awareness_type.split(".")[0] if "." in awareness_type else awareness_type, "other")

        # Build identifier
        warning_id = props.get("identifier", props.get("id", ""))
        if not warning_id:
            return None

        # Extract text
        headline = props.get("headline", "")
        description = props.get("description", "")
        instruction = props.get("instruction", "")

        # Area name
        area_name = props.get("geocode_name", props.get("area", ""))

        # Timestamps
        effective = props.get("effective", props.get("onset", ""))
        expires = props.get("expires", "")

        # Convert GeoJSON geometry to WKT
        wkt = self._geojson_geometry_to_wkt(geometry) if geometry else None

        return {
            "source": "meteoalarm",
            "source_id": f"meteoalarm-{warning_id}",
            "event_type": event_type,
            "severity": severity,
            "title": headline or f"Aviso MeteoAlarm — {area_name}",
            "description": description,
            "instructions": instruction,
            "area_wkt": wkt,
            "area_name": area_name,
            "effective": effective,
            "expires": expires,
            "source_url": "https://meteoalarm.org",
            "raw_data": feature,
        }

    @staticmethod
    def _geojson_geometry_to_wkt(geometry: dict) -> Optional[str]:
        """Convert a GeoJSON geometry object to WKT string."""
        try:
            from shapely.geometry import shape
            geom = shape(geometry)
            return geom.wkt
        except Exception:
            return None
