"""Conector DGT de Tráfico — parsea XML DATEX2 v3.6 para incidencias de tráfico."""

import logging
import xml.etree.ElementTree as ET
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Endpoint oficial NAP DATEX2 v3.6 (público, sin autenticación)
DGT_V36_URL = "https://nap.dgt.es/datex2/v3/dgt/SituationPublication/datex2_v36.xml"

# Namespaces DATEX2 v3.6 de la DGT
NS = {
    "d2": "http://levelC/schema/3/d2Payload",
    "sit": "http://levelC/schema/3/situation",
    "com": "http://levelC/schema/3/common",
    "loc": "http://levelC/schema/3/locationReferencing",
    "lse": "http://levelC/schema/3/locationReferencingSpanishExtension",
    "sse": "http://levelC/schema/3/situationSpanishExtension",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

XSI_TYPE = f"{{{NS['xsi']}}}type"

# Mapeo de severidad DATEX2
DATEX_SEVERITY_MAP = {
    "highest": "red",
    "high": "orange",
    "medium": "yellow",
    "low": "green",
    "lowest": "green",
    "none": "green",
}

# Mapeo causeType → tipo de evento interno
CAUSE_TYPE_MAP = {
    "accident": "traffic_accident",
    "roadMaintenance": "traffic_works",
    "congestion": "traffic_jam",
    "infrastructureDamageObstruction": "traffic_closure",
    "obstruction": "traffic_closure",
    "abnormalTraffic": "traffic_jam",
    "poorEnvironmentConditions": "traffic_closure",
    "animalPresenceObstruction": "traffic_closure",
}

# Mapeo xsi:type del record → tipo de evento (fallback)
RECORD_TYPE_MAP = {
    "RoadOrCarriagewayOrLaneManagement": "traffic_closure",
    "GenericSituationRecord": "traffic_closure",
    "NonWeatherRelatedRoadConditions": "traffic_closure",
    "SpeedManagement": "traffic_closure",
    "GeneralObstruction": "traffic_closure",
    "PoorEnvironmentConditions": "traffic_closure",
    "GeneralInstructionOrMessageToRoadUsers": "traffic_closure",
    "AbnormalTraffic": "traffic_jam",
    "AnimalPresenceObstruction": "traffic_closure",
    "Accident": "traffic_accident",
    "MaintenanceWorks": "traffic_works",
    "ConstructionWorks": "traffic_works",
}


class DGTConnector:
    """
    Obtiene incidencias de tráfico del feed DATEX2 v3.6 del NAP de la DGT.

    La DGT publica un SituationPublication con ~600 incidencias activas
    en carreteras españolas (excepto País Vasco y Cataluña).
    """

    async def fetch_incidents(self) -> list[dict]:
        """Obtiene y parsea todas las incidencias de tráfico activas."""
        events = []

        try:
            xml_bytes = await self._download_feed()
            if xml_bytes:
                events = self._parse_datex2_v36(xml_bytes)
        except Exception as e:
            logger.exception("Error obteniendo incidencias DGT: %s", e)

        logger.info("DGT: obtenidas %d incidencias de tráfico", len(events))
        return events

    async def _download_feed(self) -> Optional[bytes]:
        """Descarga el feed XML DATEX2 v3.6."""
        async with httpx.AsyncClient(timeout=90) as client:
            try:
                resp = await client.get(DGT_V36_URL)
                if resp.status_code == 200:
                    return resp.content
                logger.warning("NAP DGT v3.6 devuelve %s", resp.status_code)
            except Exception as e:
                logger.error("Error descargando feed DGT v3.6: %s", e)
        return None

    def _parse_datex2_v36(self, xml_bytes: bytes) -> list[dict]:
        """Parsea XML DATEX2 v3.6 SituationPublication con ElementTree."""
        events = []

        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as e:
            logger.error("Error parseando XML DATEX2 v3.6: %s", e)
            return events

        for situation in root.findall("sit:situation", NS):
            try:
                event = self._parse_situation(situation)
                if event:
                    events.append(event)
            except Exception as e:
                sit_id = situation.get("id", "?")
                logger.warning("Error parseando situación DGT %s: %s", sit_id, e)

        return events

    def _parse_situation(self, situation: ET.Element) -> Optional[dict]:
        """Parsea un elemento <sit:situation> de DATEX2 v3.6."""
        sit_id = situation.get("id", "")

        # Severidad general de la situación
        overall_sev_el = situation.find("sit:overallSeverity", NS)
        overall_severity = overall_sev_el.text if overall_sev_el is not None else "medium"

        # Primer situationRecord
        record = situation.find("sit:situationRecord", NS)
        if record is None:
            return None

        # Tipo de record (xsi:type)
        record_type_raw = record.get(XSI_TYPE, "")
        # Quitar prefijo namespace "sit:"
        record_type = record_type_raw.split(":")[-1] if ":" in record_type_raw else record_type_raw

        # Tipo de evento basado en causeType → fallback por xsi:type
        event_type = self._resolve_event_type(record, record_type)

        # Severidad del record
        sev_el = record.find("sit:severity", NS)
        severity_str = sev_el.text if sev_el is not None else overall_severity
        severity = DATEX_SEVERITY_MAP.get(severity_str.lower(), "yellow")

        # Ubicación: coordenadas + información de carretera
        lat, lon, road_name, province, municipality = self._extract_location(record)

        # Timestamps
        validity = record.find("sit:validity", NS)
        start_time = ""
        end_time = ""
        if validity is not None:
            time_spec = validity.find("com:validityTimeSpecification", NS)
            if time_spec is not None:
                st = time_spec.find("com:overallStartTime", NS)
                et = time_spec.find("com:overallEndTime", NS)
                start_time = st.text if st is not None else ""
                end_time = et.text if et is not None else ""

        # Construir título con carretera y municipio
        title = self._build_title(event_type, road_name, municipality, province)

        # Construir descripción
        description = self._build_description(event_type, road_name, municipality, province)

        wkt = f"POINT({lon} {lat})" if lat and lon else None

        # Construir nombre de área
        area_parts = [p for p in [road_name, municipality, province] if p]
        area_name = " — ".join(area_parts) if area_parts else ""

        return {
            "source": "dgt",
            "source_id": f"dgt-{sit_id}",
            "event_type": event_type,
            "severity": severity,
            "title": title,
            "description": description,
            "instructions": self._get_traffic_instructions(event_type),
            "area_wkt": wkt,
            "area_name": area_name,
            "effective": start_time,
            "expires": end_time,
            "source_url": "https://infocar.dgt.es/etraffic/",
            "raw_data": {"situation_id": sit_id, "record_type": record_type},
        }

    def _resolve_event_type(self, record: ET.Element, record_type: str) -> str:
        """Determina el tipo de evento a partir de causeType y record type."""
        cause = record.find("sit:cause", NS)
        if cause is not None:
            cause_type_el = cause.find("sit:causeType", NS)
            if cause_type_el is not None and cause_type_el.text:
                mapped = CAUSE_TYPE_MAP.get(cause_type_el.text)
                if mapped:
                    return mapped

                # Si causeType tiene 'roadworks' en detailedCauseType
                detailed = cause.find("sit:detailedCauseType", NS)
                if detailed is not None:
                    maint = detailed.find("sit:roadMaintenanceType", NS)
                    if maint is not None and "roadworks" in (maint.text or ""):
                        return "traffic_works"

        return RECORD_TYPE_MAP.get(record_type, "traffic_closure")

    def _extract_location(self, record: ET.Element) -> tuple:
        """Extrae coordenadas, carretera, provincia y municipio del record."""
        lat = lon = None
        road_name = ""
        province = ""
        municipality = ""

        loc_ref = record.find("sit:locationReference", NS)
        if loc_ref is None:
            return lat, lon, road_name, province, municipality

        # Información de carretera
        road_info = loc_ref.find(".//loc:roadInformation/loc:roadName", NS)
        if road_info is not None and road_info.text:
            road_name = road_info.text

        # Coordenadas del primer punto (from o to)
        for point_path in [
            ".//loc:tpegLinearLocation/loc:from/loc:pointCoordinates",
            ".//loc:tpegLinearLocation/loc:to/loc:pointCoordinates",
            ".//loc:pointCoordinates",
        ]:
            coords = loc_ref.find(point_path, NS)
            if coords is not None:
                lat_el = coords.find("loc:latitude", NS)
                lon_el = coords.find("loc:longitude", NS)
                if lat_el is not None and lon_el is not None:
                    try:
                        lat = float(lat_el.text)
                        lon = float(lon_el.text)
                    except (ValueError, TypeError):
                        pass
                    break

        # Extensiones españolas: provincia y municipio
        for ext in loc_ref.findall(".//loc:extendedTpegNonJunctionPoint", NS):
            prov_el = ext.find("lse:province", NS)
            muni_el = ext.find("lse:municipality", NS)
            if prov_el is not None and prov_el.text:
                province = prov_el.text
            if muni_el is not None and muni_el.text:
                municipality = muni_el.text
            if province:
                break

        return lat, lon, road_name, province, municipality

    @staticmethod
    def _build_title(event_type: str, road_name: str, municipality: str, province: str) -> str:
        """Construye título legible para la incidencia."""
        type_labels = {
            "traffic_accident": "🚗 Accidente",
            "traffic_closure": "🚧 Restricción vial",
            "traffic_works": "🔧 Obras",
            "traffic_jam": "🐌 Retención",
        }
        label = type_labels.get(event_type, "🚗 Incidencia")
        parts = [p for p in [road_name, municipality] if p]
        if parts:
            return f"{label} — {', '.join(parts)}"
        return label

    @staticmethod
    def _build_description(event_type: str, road_name: str, municipality: str, province: str) -> str:
        """Construye descripción detallada."""
        parts = []
        if road_name:
            parts.append(f"Carretera: {road_name}")
        if municipality:
            parts.append(f"Municipio: {municipality}")
        if province:
            parts.append(f"Provincia: {province}")
        return ". ".join(parts) if parts else "Incidencia de tráfico"

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
                "🚧 Restricción vial\n"
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
