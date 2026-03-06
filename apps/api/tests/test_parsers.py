"""Tests for connector parsers with real XML/CSV fixtures.

Verifies that AEMET, IGN, and DGT parsers produce correct normalized events
from representative sample data.
"""

from pathlib import Path

from app.connectors.aemet import AemetConnector
from app.connectors.ign import IGNConnector, magnitude_to_severity
from app.connectors.dgt import DGTConnector

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ── AEMET CAP XML ────────────────────────────────────────────


class TestAemetParser:
    """Tests for the AEMET CAP XML parser."""

    def setup_method(self):
        self.connector = AemetConnector()
        self.xml = (FIXTURES_DIR / "aemet_cap_sample.xml").read_text(encoding="utf-8")

    def test_parse_returns_events(self):
        """Parser should return at least one event from the sample XML."""
        events = self.connector._parse_cap_xml(self.xml, "61")
        assert len(events) >= 1

    def test_event_fields(self):
        """Each event has the mandatory normalizer fields."""
        events = self.connector._parse_cap_xml(self.xml, "61")
        event = events[0]

        required_fields = [
            "source",
            "source_id",
            "event_type",
            "severity",
            "title",
            "description",
            "area_name",
            "effective",
            "expires",
        ]
        for field in required_fields:
            assert field in event, f"Missing required field: {field}"

    def test_event_source_is_aemet(self):
        """Source must be 'aemet'."""
        events = self.connector._parse_cap_xml(self.xml, "61")
        assert events[0]["source"] == "aemet"

    def test_event_type_mapping(self):
        """Type 'Viento' must map to 'wind'."""
        events = self.connector._parse_cap_xml(self.xml, "61")
        assert events[0]["event_type"] == "wind"

    def test_severity_mapping(self):
        """Severity 'Moderate' must map to 'yellow'."""
        events = self.connector._parse_cap_xml(self.xml, "61")
        assert events[0]["severity"] == "yellow"

    def test_polygon_parsed(self):
        """XML polygon is converted to WKT."""
        events = self.connector._parse_cap_xml(self.xml, "61")
        wkt = events[0].get("area_wkt")
        assert wkt is not None
        assert wkt.startswith("POLYGON((")

    def test_area_name(self):
        """Area name is extracted correctly."""
        events = self.connector._parse_cap_xml(self.xml, "61")
        assert events[0]["area_name"] == "Sierra de Madrid"

    def test_cap_polygon_to_wkt_empty(self):
        """An empty polygon returns None."""
        assert AemetConnector._cap_polygon_to_wkt("") is None
        assert AemetConnector._cap_polygon_to_wkt(None) is None

    def test_cap_polygon_to_wkt_valid(self):
        """Valid polygon is converted to WKT with inverted coordinates."""
        # CAP uses lat,lon — WKT uses lon lat
        wkt = AemetConnector._cap_polygon_to_wkt("40.0,-3.0 41.0,-3.0 41.0,-2.0 40.0,-3.0")
        assert wkt == "POLYGON((-3.0 40.0, -3.0 41.0, -2.0 41.0, -3.0 40.0))"


# ── IGN FDSN Text ────────────────────────────────────────────


class TestIGNParser:
    """Tests for the IGN FDSN text parser."""

    def setup_method(self):
        self.connector = IGNConnector()
        self.text = (FIXTURES_DIR / "ign_fdsn_sample.txt").read_text(encoding="utf-8")

    def test_parse_returns_events(self):
        """Should parse the 5 earthquakes from the fixture."""
        events = self.connector._parse_fdsn_text(self.text)
        assert len(events) == 5

    def test_event_fields(self):
        """Events have all required fields."""
        events = self.connector._parse_fdsn_text(self.text)
        required_fields = [
            "source",
            "source_id",
            "event_type",
            "severity",
            "title",
            "magnitude",
            "depth_km",
            "area_wkt",
        ]
        for field in required_fields:
            assert field in events[0], f"Missing field: {field}"

    def test_source_is_ign(self):
        """Source must be 'ign'."""
        events = self.connector._parse_fdsn_text(self.text)
        assert all(e["source"] == "ign" for e in events)

    def test_event_type_is_earthquake(self):
        """All events are of type 'earthquake'."""
        events = self.connector._parse_fdsn_text(self.text)
        assert all(e["event_type"] == "earthquake" for e in events)

    def test_magnitude_parsed(self):
        """Magnitudes are parsed correctly."""
        events = self.connector._parse_fdsn_text(self.text)
        magnitudes = [e["magnitude"] for e in events]
        assert "3.2" in magnitudes
        assert "4.5" in magnitudes

    def test_severity_by_magnitude(self):
        """Severity is calculated correctly based on magnitude."""
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
        """Geometry is a WKT point."""
        events = self.connector._parse_fdsn_text(self.text)
        for e in events:
            assert e["area_wkt"].startswith("POINT(")

    def test_location_name(self):
        """Locations are extracted correctly from the last field."""
        events = self.connector._parse_fdsn_text(self.text)
        locations = [e["area_name"] for e in events]
        assert "S GRANADA.GR" in locations
        assert "ASTURIAS" in locations


class TestMagnitudeToSeverity:
    """Direct tests for the magnitude_to_severity function."""

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
    """Tests for the DGT DATEX2 v3.6 XML parser."""

    def setup_method(self):
        self.connector = DGTConnector()
        self.xml_bytes = (FIXTURES_DIR / "dgt_datex2_sample.xml").read_bytes()

    def test_parse_returns_events(self):
        """Should parse the 2 situations from the v3.6 fixture."""
        events = self.connector._parse_datex2_v36(self.xml_bytes)
        assert len(events) == 2

    def test_event_has_required_fields(self):
        """Events have the mandatory fields."""
        events = self.connector._parse_datex2_v36(self.xml_bytes)
        required = ["source", "source_id", "event_type", "severity", "title"]
        for field in required:
            assert field in events[0], f"Missing field: {field}"

    def test_source_is_dgt(self):
        """Source must be 'dgt'."""
        events = self.connector._parse_datex2_v36(self.xml_bytes)
        assert all(e["source"] == "dgt" for e in events)

    def test_accident_severity(self):
        """Accident with severity 'high' maps to 'orange'."""
        events = self.connector._parse_datex2_v36(self.xml_bytes)
        accident = next((e for e in events if e["event_type"] == "traffic_accident"), None)
        assert accident is not None, "Should have an accident"
        assert accident["severity"] == "orange"

    def test_works_type(self):
        """Situation with causeType roadMaintenance maps to traffic_works."""
        events = self.connector._parse_datex2_v36(self.xml_bytes)
        works = next((e for e in events if e["event_type"] == "traffic_works"), None)
        assert works is not None, "Should have works"
        assert works["severity"] == "green"

    def test_coordinates_extracted(self):
        """Coordinates are extracted correctly."""
        events = self.connector._parse_datex2_v36(self.xml_bytes)
        accident = next(e for e in events if e["event_type"] == "traffic_accident")
        assert accident["area_wkt"] is not None
        assert "40.4168" in accident["area_wkt"]
        assert "-3.7038" in accident["area_wkt"]

    def test_road_name_extracted(self):
        """Road name is extracted from roadInformation."""
        events = self.connector._parse_datex2_v36(self.xml_bytes)
        assert any("A-6" in (e.get("area_name") or "") for e in events)
        assert any("GR-5202" in (e.get("area_name") or "") for e in events)

    def test_province_in_area_name(self):
        """Province is included in area_name."""
        events = self.connector._parse_datex2_v36(self.xml_bytes)
        assert any("Madrid" in (e.get("area_name") or "") for e in events)
        assert any("Granada" in (e.get("area_name") or "") for e in events)
