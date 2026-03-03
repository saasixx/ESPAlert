"""Tests para validación de esquemas Pydantic."""

import pytest
from pydantic import ValidationError

from app.schemas.auth import UserCreate, UserLogin, UserSettingsUpdate
from app.schemas.event import EventOut, EventListParams
from app.schemas.subscription import ZoneCreate, FilterCreate
from app.schemas.report import ReportCreate


class TestUserCreate:
    def test_valid_user(self):
        user = UserCreate(email="test@example.com", password="Abc12345")
        assert user.email == "test@example.com"

    def test_weak_password_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com", password="12345678")  # Sin mayúscula ni minúscula

    def test_short_password_rejected(self):
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com", password="Abc1")

    def test_html_stripped_from_name(self):
        user = UserCreate(email="a@b.com", password="Abc12345", display_name="<script>alert</script>Juan")
        assert "<" not in user.display_name

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(email="not-an-email", password="Abc12345")


class TestEventListParams:
    def test_defaults(self):
        params = EventListParams()
        assert params.active_only is True
        assert params.limit == 50

    def test_invalid_severity(self):
        with pytest.raises(ValidationError):
            EventListParams(severity="extreme")

    def test_valid_severity(self):
        params = EventListParams(severity="red")
        assert params.severity == "red"

    def test_lat_out_of_range(self):
        with pytest.raises(ValidationError):
            EventListParams(lat=80.0)  # Fuera de España


class TestZoneCreate:
    def test_valid_zone(self):
        zone = ZoneCreate(label="Casa", geojson={"type": "Point", "coordinates": [-3.7, 40.4]})
        assert zone.label == "Casa"

    def test_missing_geojson_type(self):
        with pytest.raises(ValidationError):
            ZoneCreate(label="Test", geojson={"coordinates": [0, 0]})

    def test_too_large_geojson(self):
        # Generar GeoJSON > 100KB
        huge = {"type": "Polygon", "coordinates": [[[i * 0.001, i * 0.001] for i in range(20000)]]}
        with pytest.raises(ValidationError):
            ZoneCreate(label="Huge", geojson=huge)


class TestFilterCreate:
    def test_valid_filter(self):
        f = FilterCreate(min_severity="orange", event_types=["meteo", "seismic"])
        assert f.min_severity == "orange"

    def test_invalid_severity(self):
        with pytest.raises(ValidationError):
            FilterCreate(min_severity="extreme")

    def test_invalid_event_type(self):
        with pytest.raises(ValidationError):
            FilterCreate(event_types=["invalid_type"])


class TestReportCreate:
    def test_valid_report(self):
        r = ReportCreate(report_type="rain", intensity="strong", lat=40.0, lon=-3.5)
        assert r.report_type == "rain"

    def test_invalid_report_type(self):
        with pytest.raises(ValidationError):
            ReportCreate(report_type="explosion", intensity="strong", lat=40.0, lon=-3.5)

    def test_invalid_intensity(self):
        with pytest.raises(ValidationError):
            ReportCreate(report_type="rain", intensity="apocalyptic", lat=40.0, lon=-3.5)

    def test_comment_sanitized(self):
        r = ReportCreate(report_type="rain", intensity="light", lat=40.0, lon=-3.5, comment="<b>Hello</b>")
        assert "<" not in r.comment
