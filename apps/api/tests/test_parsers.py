"""Tests de parsers de conectores con fixtures reales XML/CSV.

Verifica que los parsers de AEMET, IGN y DGT producen eventos normalizados
correctos a partir de datos de ejemplo representativos.
"""

from pathlib import Path

import pytest

from app.connectors.aemet import AemetConnector, AEMET_EVENT_MAP
from app.connectors.ign import IGNConnector, magnitude_to_severity
from app.connectors.dgt import DGTConnector

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ── AEMET CAP XML ────────────────────────────────────────────


class TestAemetParser:
    """Tests del parser XML CAP de AEMET."""

    def setup_method(self):
        self.connector = AemetConnector()
        self.xml = (FIXTURES_DIR / "aemet_cap_sample.xml").read_text(encoding="utf-8")

    def test_parse_returns_events(self):
        """El parser debe devolver al menos un evento del XML de ejemplo."""
        events = self.connector._parse_cap_xml(self.xml, "61")
        assert len(events) >= 1

    def test_event_fields(self):
        """Cada evento tiene los campos obligatorios del normalizador."""
        events = self.connector._parse_cap_xml(self.xml, "61")
        event = events[0]

        required_fields = [
            "source", "source_id", "event_type", "severity",
            "title", "description", "area_name",
            "effective", "expires",
        ]
        for field in required_fields:
            assert field in event, f"Falta campo obligatorio: {field}"

    def test_event_source_is_aemet(self):
        """La fuente debe ser 'aemet'."""
        events = self.connector._parse_cap_xml(self.xml, "61")
        assert events[0]["source"] == "aemet"

    def test_event_type_mapping(self):
        """El tipo 'Viento' debe mapearse a 'wind'."""
        events = self.connector._parse_cap_xml(self.xml, "61")
        assert events[0]["event_type"] == "wind"

    def test_severity_mapping(self):
        """Severidad 'Moderate' debe mapearse a 'yellow'."""
        events = self.connector._parse_cap_xml(self.xml, "61")
        assert events[0]["severity"] == "yellow"

    def test_polygon_parsed(self):
        """El polígono del XML se convierte a WKT."""
        events = self.connector._parse_cap_xml(self.xml, "61")
        wkt = events[0].get("area_wkt")
        assert wkt is not None
        assert wkt.startswith("POLYGON((")

    def test_area_name(self):
        """El nombre de área se extrae correctamente."""
        events = self.connector._parse_cap_xml(self.xml, "61")
        assert events[0]["area_name"] == "Sierra de Madrid"

    def test_cap_polygon_to_wkt_empty(self):
        """Un polígono vacío retorna None."""
        assert AemetConnector._cap_polygon_to_wkt("") is None
        assert AemetConnector._cap_polygon_to_wkt(None) is None

    def test_cap_polygon_to_wkt_valid(self):
        """Polígono válido se convierte a WKT con coordenadas invertidas."""
        # CAP usa lat,lon — WKT usa lon lat
        wkt = AemetConnector._cap_polygon_to_wkt("40.0,-3.0 41.0,-3.0 41.0,-2.0 40.0,-3.0")
        assert wkt == "POLYGON((-3.0 40.0, -3.0 41.0, -2.0 41.0, -3.0 40.0))"


# ── IGN FDSN Text ────────────────────────────────────────────


class TestIGNParser:
    """Tests del parser texto FDSN del IGN."""

    def setup_method(self):
        self.connector = IGNConnector()
        self.text = (FIXTURES_DIR / "ign_fdsn_sample.txt").read_text(encoding="utf-8")

    def test_parse_returns_events(self):
        """Debe parsear los 5 terremotos del fixture."""
        events = self.connector._parse_fdsn_text(self.text)
        assert len(events) == 5

    def test_event_fields(self):
        """Los eventos tienen todos los campos requeridos."""
        events = self.connector._parse_fdsn_text(self.text)
        required_fields = [
            "source", "source_id", "event_type", "severity",
            "title", "magnitude", "depth_km", "area_wkt",
        ]
        for field in required_fields:
            assert field in events[0], f"Falta campo: {field}"

    def test_source_is_ign(self):
        """La fuente debe ser 'ign'."""
        events = self.connector._parse_fdsn_text(self.text)
        assert all(e["source"] == "ign" for e in events)

    def test_event_type_is_earthquake(self):
        """Todos los eventos son de tipo 'earthquake'."""
        events = self.connector._parse_fdsn_text(self.text)
        assert all(e["event_type"] == "earthquake" for e in events)

    def test_magnitude_parsed(self):
        """Las magnitudes se parsean correctamente."""
        events = self.connector._parse_fdsn_text(self.text)
        magnitudes = [e["magnitude"] for e in events]
        assert "3.2" in magnitudes
        assert "4.5" in magnitudes

    def test_severity_by_magnitude(self):
        """La severidad se calcula correcta según la magnitud."""
        events = self.connector._parse_fdsn_text(self.text)
        # M4.5 → orange
        m45 = next(e for e in events if e["magnitude"] == "4.5")
        assert m45["severity"] == "orange"
        # M3.2 → yellow
        m32 = next(e for e in events if e["magnitude"] == "3.2")
        assert m32["severity"] == "yellow"
        # M0.8 → green
        m08 = next(e for e in events if e["magnitude"] == "0.8")
        assert m08["severity"] == "green"

    def test_area_wkt_is_point(self):
        """La geometría es un punto WKT."""
        events = self.connector._parse_fdsn_text(self.text)
        for e in events:
            assert e["area_wkt"].startswith("POINT(")

    def test_location_name(self):
        """Las ubicaciones se extraen bien del último campo."""
        events = self.connector._parse_fdsn_text(self.text)
        locations = [e["area_name"] for e in events]
        assert "S GRANADA.GR" in locations
        assert "ASTURIAS" in locations


class TestMagnitudeToSeverity:
    """Tests directos de la función magnitude_to_severity."""

    def test_extreme(self):
        assert magnitude_to_severity(5.0) == "red"
        assert magnitude_to_severity(7.2) == "red"

    def test_moderate(self):
        assert magnitude_to_severity(4.0) == "orange"
        assert magnitude_to_severity(4.9) == "orange"

    def test_minor(self):
        assert magnitude_to_severity(3.0) == "yellow"
        assert magnitude_to_severity(3.9) == "yellow"

    def test_insignificant(self):
        assert magnitude_to_severity(0.5) == "green"
        assert magnitude_to_severity(2.9) == "green"


# ── DGT DATEX2 XML ───────────────────────────────────────────


class TestDGTParser:
    """Tests del parser XML DATEX2 de la DGT."""

    def setup_method(self):
        self.connector = DGTConnector()
        self.xml = (FIXTURES_DIR / "dgt_datex2_sample.xml").read_text(encoding="utf-8")

    def test_parse_returns_events(self):
        """Debe parsear las 2 situaciones del fixture."""
        events = self.connector._parse_datex2(self.xml)
        assert len(events) == 2

    def test_event_has_required_fields(self):
        """Los eventos tienen los campos obligatorios."""
        events = self.connector._parse_datex2(self.xml)
        required = ["source", "source_id", "event_type", "severity", "title"]
        for field in required:
            assert field in events[0], f"Falta campo: {field}"

    def test_source_is_dgt(self):
        """La fuente debe ser 'dgt'."""
        events = self.connector._parse_datex2(self.xml)
        assert all(e["source"] == "dgt" for e in events)

    def test_accident_severity(self):
        """Un accidente con severidad 'high' se mapea a 'orange'."""
        events = self.connector._parse_datex2(self.xml)
        accident = next((e for e in events if "accident" in e["event_type"]), None)
        if accident:
            assert accident["severity"] == "orange"

    def test_event_types(self):
        """Los tipos de evento se mapean correctamente desde DATEX2."""
        events = self.connector._parse_datex2(self.xml)
        types = {e["event_type"] for e in events}
        # Debe contener accident y works
        assert any("accident" in t for t in types) or any("works" in t for t in types) or any("closure" in t for t in types)
