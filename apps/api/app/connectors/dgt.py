"""Conector DGT de Tráfico — parsea XML DATEX2 v3.6 para incidencias de tráfico."""

import logging
from typing import Optional

import httpx
import xmltodict

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Endpoint NAP de la DGT para incidencias de tráfico (DATEX2)
# Requiere registro gratuito en https://nap.dgt.es para obtener credenciales API
DGT_INCIDENTS_URL = "https://nap.dgt.es/api/datex/v3/incidents"
DGT_INCIDENTS_FALLBACK = "https://infocar.dgt.es/datex2/dgt/SituationPublication/all/content.xml"

# Mapeo de severidad DATEX2
DATEX_SEVERITY_MAP = {
    "highest": "red",
    "high": "orange",
    "medium": "yellow",
    "low": "green",
    "lowest": "green",
    "none": "green",
}

# Tipo de registro DATEX2 → nuestro tipo de evento
DATEX_TYPE_MAP = {
    "Accident": "traffic_accident",
    "AbnormalTraffic": "traffic_jam",
    "MaintenanceWorks": "traffic_works",
    "RoadOrCarriagewayOrLaneManagementType": "traffic_closure",
    "ReroutingManagement": "traffic_closure",
    "NetworkManagement": "traffic_closure",
    "RoadConditions": "traffic_closure",
    "ConstructionWorks": "traffic_works",
    "GeneralObstruction": "traffic_closure",
    "VehicleObstruction": "traffic_accident",
}


class DGTConnector:
    """
    Obtiene incidencias de tráfico de los feeds DATEX2 de la DGT.

    La DGT publica documentos situationPublication en formato XML DATEX2
    que contienen información sobre accidentes, cortes y obras.
    """

    async def fetch_incidents(self) -> list[dict]:
        """Obtiene y parsea todas las incidencias de tráfico activas."""
        events = []

        try:
            xml_text = await self._download_feed()
            if xml_text:
                events = self._parse_datex2(xml_text)
        except Exception as e:
            logger.exception("Error obteniendo incidencias DGT: %s", e)

        logger.info("DGT: obtenidas %d incidencias de tráfico", len(events))
        return events

    async def _download_feed(self) -> Optional[str]:
        """Descarga el feed XML DATEX2."""
        async with httpx.AsyncClient(timeout=60) as client:
            # Intentar primero el endpoint NAP principal
            try:
                resp = await client.get(DGT_INCIDENTS_URL)
                if resp.status_code == 200:
                    return resp.text
                logger.warning("NAP DGT devuelve %s, intentando fallback...", resp.status_code)
            except Exception as e:
                logger.warning("NAP DGT falló: %s, intentando fallback...", e)

            # Fallback al endpoint de infocar
            try:
                resp = await client.get(DGT_INCIDENTS_FALLBACK)
                if resp.status_code == 200:
                    return resp.text
            except Exception as e:
                logger.error("Fallback DGT también falló: %s", e)

        return None

    def _parse_datex2(self, xml_text: str) -> list[dict]:
        """Parsea XML SituationPublication DATEX2."""
        events = []

        try:
            # Eliminar namespaces XML para facilitar el parseo
            xml_clean = xml_text.replace('xmlns=', 'xmlns_disabled=')
            parsed = xmltodict.parse(xml_clean)
        except Exception as e:
            logger.error("Error al parsear XML DATEX2: %s", e)
            return events

        # Navegar a situaciones
        publication = parsed.get("d2LogicalModel", parsed)
        if isinstance(publication, dict):
            publication = publication.get("payloadPublication", publication)

        situations = publication.get("situation", [])
        if isinstance(situations, dict):
            situations = [situations]

        for situation in situations:
            try:
                event = self._parse_situation(situation)
                if event:
                    events.append(event)
            except Exception as e:
                logger.warning("Error al parsear situación DATEX2: %s", e)

        return events

    def _parse_situation(self, situation: dict) -> Optional[dict]:
        """Parsea un solo elemento DATEX2 <situation>."""
        sit_id = situation.get("@id", "")

        records = situation.get("situationRecord", [])
        if isinstance(records, dict):
            records = [records]

        if not records:
            return None

        record = records[0]  # Registro principal

        # Extraer tipo
        record_type = record.get("@xsi:type", record.get("@type", ""))
        event_type = "traffic_closure"
        for key, value in DATEX_TYPE_MAP.items():
            if key.lower() in record_type.lower():
                event_type = value
                break

        # Extraer severidad
        severity_str = record.get("severity", "medium")
        if isinstance(severity_str, dict):
            severity_str = severity_str.get("#text", "medium")
        severity = DATEX_SEVERITY_MAP.get(severity_str.lower(), "yellow")

        # Extraer ubicación
        location = record.get("groupOfLocations", {})
        point = location.get("locationForDisplay", {})
        lat = None
        lon = None
        if point:
            lat = float(point.get("latitude", 0))
            lon = float(point.get("longitude", 0))

        # Extraer descripción
        general_comment = record.get("generalPublicComment", {})
        comment_value = ""
        if isinstance(general_comment, dict):
            comment_multilingual = general_comment.get("comment", {}).get("value", {})
            if isinstance(comment_multilingual, dict):
                comment_value = comment_multilingual.get("#text", "")
            elif isinstance(comment_multilingual, list):
                for val in comment_multilingual:
                    if isinstance(val, dict) and val.get("@lang") == "es":
                        comment_value = val.get("#text", "")
                        break

        # Extraer información de carretera
        road_name = ""
        linear_element = location.get("linearElement", {})
        if linear_element:
            road_info = linear_element.get("roadName", {})
            if isinstance(road_info, dict):
                road_name = road_info.get("value", {}).get("#text", "")

        # Construir título
        type_labels = {
            "traffic_accident": "🚗 Accidente",
            "traffic_closure": "🚧 Corte de carretera",
            "traffic_works": "🔧 Obras",
            "traffic_jam": "🐌 Retención",
        }
        title = f"{type_labels.get(event_type, '🚗 Incidencia')} — {road_name}" if road_name else type_labels.get(event_type, "Incidencia de tráfico")

        # Marcas de tiempo
        validity = record.get("validity", {})
        valid_period = validity.get("validityTimeSpecification", {})
        start_time = valid_period.get("overallStartTime", "")
        end_time = valid_period.get("overallEndTime", "")

        wkt = f"POINT({lon} {lat})" if lat and lon else None

        return {
            "source": "dgt",
            "source_id": f"dgt-{sit_id}",
            "event_type": event_type,
            "severity": severity,
            "title": title,
            "description": comment_value or f"Incidencia en {road_name}",
            "instructions": self._get_traffic_instructions(event_type),
            "area_wkt": wkt,
            "area_name": road_name,
            "effective": start_time,
            "expires": end_time,
            "source_url": "https://infocar.dgt.es/etraffic/",
            "raw_data": situation,
        }

    @staticmethod
    def _get_traffic_instructions(event_type: str) -> str:
        instructions = {
            "traffic_accident": (
                "⚠️ Accidente de tráfico\n"
                "• Reduzca la velocidad al acercarse\n"
                "• No se detenga a mirar (efecto mirón)\n"
                "• Siga las indicaciones de los agentes\n"
                "• Considere rutas alternativas"
            ),
            "traffic_closure": (
                "🚧 Carretera cortada\n"
                "• Busque una ruta alternativa\n"
                "• Consulte el mapa de tráfico DGT\n"
                "• Si está atrapado, mantenga la calma y espere indicaciones"
            ),
            "traffic_works": (
                "🔧 Obras en la vía\n"
                "• Reduzca la velocidad en la zona de obras\n"
                "• Preste atención a la señalización temporal\n"
                "• Puede haber desvíos provisionales"
            ),
            "traffic_jam": (
                "🐌 Retención de tráfico\n"
                "• Considere salir en la próxima salida disponible\n"
                "• Mantenga la distancia de seguridad\n"
                "• Encienda las luces de emergencia si se detiene bruscamente"
            ),
        }
        return instructions.get(event_type, "Mantenga la precaución al circular.")
