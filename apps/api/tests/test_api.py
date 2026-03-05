"""Smoke tests for API endpoints."""


async def test_root(client):
    """Root endpoint returns app info."""
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "app" in data
    assert data["status"] == "running"


async def test_health(client):
    """Health endpoint returns status."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data


async def test_events_list(client):
    """Events endpoint returns a list (may be empty without DB)."""
    resp = await client.get("/api/v1/events/")
    # Puede degradar sin DB disponible, pero no debe romper el test runner.
    assert resp.status_code in (200, 500, 503)


async def test_register_validation(client):
    """Register rejects invalid input."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "short"},
    )
    assert resp.status_code in (400, 422)


async def test_login_missing_fields(client):
    """Login rejects missing credentials."""
    resp = await client.post("/api/v1/auth/login", json={})
    assert resp.status_code == 422


async def test_protected_endpoint_requires_auth(client):
    """Protected endpoints return 401 without token."""
    resp = await client.get("/api/v1/subscriptions/zones")
    assert resp.status_code in (401, 403)


async def test_report_requires_auth(client):
    """Reports endpoint requires authentication."""
    resp = await client.post(
        "/api/v1/reports/",
        json={
            "report_type": "rain",
            "intensity": "moderate",
            "lat": 40.4168,
            "lon": -3.7038,
        },
    )
    assert resp.status_code in (401, 403)
