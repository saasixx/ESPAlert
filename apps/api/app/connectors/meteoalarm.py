"""MeteoAlarm connector — fetches European weather warnings via CAP/JSON feed API."""

import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# MeteoAlarm Feeds API (public, no key required)
FEEDS_URL = "https://feeds.meteoalarm.org/api/v1/warnings/feeds-spain"

# CAP severity → our severity
CAP_SEVERITY = {
    "Extreme": "red",
    "Severe": "orange",
    "Moderate": "yellow",
    "Minor": "green",
    "Unknown": "green",
}

# awareness_type parameter → our event types
AWARENESS_TYPE_MAP = {
    "1": "wind",
    "2": "snow",
    "3": "storm",
    "4": "fog",
    "5": "heat",
    "6": "cold",
    "7": "coastal",
    "8": "fire_risk",
    "9": "wave",
    "10": "rain",
    "11": "rain",
    "12": "rain",
    "13": "other",
}


class MeteoAlarmConnector:
    """
    Fetch weather warnings from the MeteoAlarm feeds API.

    Uses the CAP-based JSON feed that returns all active warnings for Spain,
    sourced from AEMET and published in the standardized European format.
    """

    async def fetch_warnings(self) -> list[dict]:
        """Fetch all active MeteoAlarm warnings for Spain."""
        events = []

        try:
            data = await self._query_feed()
            if data:
                events = self._parse_warnings(data)
        except Exception as e:
            logger.exception("Error fetching MeteoAlarm warnings: %s", e)

        logger.info("MeteoAlarm: fetched %d warnings", len(events))
        return events

    async def _query_feed(self) -> Optional[dict]:
        """Query the MeteoAlarm feeds API."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(FEEDS_URL)

            if resp.status_code != 200:
                logger.error("MeteoAlarm feeds returns %s: %s", resp.status_code, resp.text[:200])
                return None

            return resp.json()

    def _parse_warnings(self, data: dict) -> list[dict]:
        """Parse MeteoAlarm CAP/JSON warnings to our event format."""
        events = []

        warnings = data.get("warnings", [])
        for warning in warnings:
            try:
                event = self._parse_warning(warning)
                if event:
                    events.append(event)
            except Exception as e:
                logger.warning("Error parsing MeteoAlarm warning: %s", e)

        return events

    def _parse_warning(self, warning: dict) -> Optional[dict]:
        """Parse a single CAP alert warning."""
        alert = warning.get("alert", {})
        identifier = alert.get("identifier", "")
        if not identifier:
            return None

        # Get info block in Spanish (first), fallback to any
        info_list = alert.get("info", [])
        if not info_list:
            return None

        info = info_list[0]
        for i in info_list:
            if i.get("language", "").startswith("es"):
                info = i
                break

        # Skip "AllClear" — these are cancellations
        response_types = info.get("responseType", [])
        if "AllClear" in response_types:
            return None

        # Severity
        cap_severity = info.get("severity", "Minor")
        severity = CAP_SEVERITY.get(cap_severity, "green")

        # Skip green/minor alerts to reduce noise
        if severity == "green":
            return None

        # Event type from awareness_type parameter
        event_type = "other"
        params = info.get("parameter", [])
        for p in params:
            if p.get("valueName") == "awareness_type":
                # Format: "1; Wind" → take first number
                val = p.get("value", "13")
                type_num = val.split(";")[0].strip()
                event_type = AWARENESS_TYPE_MAP.get(type_num, "other")
                break

        # Text fields
        headline = info.get("headline", "")
        event_name = info.get("event", "")
        description = info.get("description", headline)

        # Area
        areas = info.get("area", [])
        area_name = areas[0].get("areaDesc", "") if areas else ""

        # Timestamps
        effective = info.get("effective", info.get("onset", ""))
        expires = info.get("expires", "")

        # Sender
        sender_name = info.get("senderName", "MeteoAlarm")

        return {
            "source": "meteoalarm",
            "source_id": f"meteoalarm-{identifier}",
            "event_type": event_type,
            "severity": severity,
            "title": headline or f"{event_name} — {area_name}",
            "description": description or event_name,
            "instructions": f"Fuente: {sender_name}",
            "area_wkt": None,  # No geometry in feeds API, only geocodes
            "area_name": area_name,
            "effective": effective,
            "expires": expires,
            "source_url": info.get("web", "https://meteoalarm.org"),
            "raw_data": warning,
        }
