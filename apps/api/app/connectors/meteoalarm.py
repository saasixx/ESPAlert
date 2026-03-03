"""Conector MeteoAlarm — obtiene avisos meteorológicos europeos vía API de feeds CAP/JSON."""

import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# API de Feeds MeteoAlarm (público, sin clave necesaria)
FEEDS_URL = "https://feeds.meteoalarm.org/api/v1/warnings/feeds-spain"

# Severidad CAP → nuestra severidad
CAP_SEVERITY = {
    "Extreme": "red",
    "Severe": "orange",
    "Moderate": "yellow",
    "Minor": "green",
    "Unknown": "green",
}

# Parámetro awareness_type → nuestros tipos de evento
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
    Obtiene avisos meteorológicos de la API de feeds de MeteoAlarm.

    Usa el feed JSON basado en CAP que retorna todos los avisos activos para España,
    procedentes de AEMET y publicados en el formato europeo estandarizado.
    """

    async def fetch_warnings(self) -> list[dict]:
        """Obtiene todos los avisos MeteoAlarm activos para España."""
        events = []

        try:
            data = await self._query_feed()
            if data:
                events = self._parse_warnings(data)
        except Exception as e:
            logger.exception("Error obteniendo avisos MeteoAlarm: %s", e)

        logger.info("MeteoAlarm: obtenidos %d avisos", len(events))
        return events

    async def _query_feed(self) -> Optional[dict]:
        """Consulta la API de feeds de MeteoAlarm."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(FEEDS_URL)

            if resp.status_code != 200:
                logger.error("MeteoAlarm feeds devuelve %s: %s", resp.status_code, resp.text[:200])
                return None

            return resp.json()

    def _parse_warnings(self, data: dict) -> list[dict]:
        """Parsea avisos CAP/JSON de MeteoAlarm a nuestro formato de evento."""
        events = []

        warnings = data.get("warnings", [])
        for warning in warnings:
            try:
                event = self._parse_warning(warning)
                if event:
                    events.append(event)
            except Exception as e:
                logger.warning("Error al parsear aviso MeteoAlarm: %s", e)

        return events

    def _parse_warning(self, warning: dict) -> Optional[dict]:
        """Parsea un solo aviso de alerta CAP."""
        alert = warning.get("alert", {})
        identifier = alert.get("identifier", "")
        if not identifier:
            return None

        # Obtener bloque info en español (primero), fallback a cualquiera
        info_list = alert.get("info", [])
        if not info_list:
            return None

        info = info_list[0]
        for i in info_list:
            if i.get("language", "").startswith("es"):
                info = i
                break

        # Omitir "AllClear" — son cancelaciones
        response_types = info.get("responseType", [])
        if "AllClear" in response_types:
            return None

        # Severidad
        cap_severity = info.get("severity", "Minor")
        severity = CAP_SEVERITY.get(cap_severity, "green")

        # Omitir alertas verdes/menores para reducir ruido
        if severity == "green":
            return None

        # Tipo de evento desde parámetro awareness_type
        event_type = "other"
        params = info.get("parameter", [])
        for p in params:
            if p.get("valueName") == "awareness_type":
                # Formato: "1; Wind" → tomar primer número
                val = p.get("value", "13")
                type_num = val.split(";")[0].strip()
                event_type = AWARENESS_TYPE_MAP.get(type_num, "other")
                break

        # Campos de texto
        headline = info.get("headline", "")
        event_name = info.get("event", "")
        description = info.get("description", headline)

        # Área
        areas = info.get("area", [])
        area_name = areas[0].get("areaDesc", "") if areas else ""

        # Marcas de tiempo
        effective = info.get("effective", info.get("onset", ""))
        expires = info.get("expires", "")

        # Emisor
        sender_name = info.get("senderName", "MeteoAlarm")

        return {
            "source": "meteoalarm",
            "source_id": f"meteoalarm-{identifier}",
            "event_type": event_type,
            "severity": severity,
            "title": headline or f"{event_name} — {area_name}",
            "description": description or event_name,
            "instructions": f"Fuente: {sender_name}",
            "area_wkt": None,  # Sin geometría en la API de feeds, solo geocódigos
            "area_name": area_name,
            "effective": effective,
            "expires": expires,
            "source_url": info.get("web", "https://meteoalarm.org"),
            "raw_data": warning,
        }
