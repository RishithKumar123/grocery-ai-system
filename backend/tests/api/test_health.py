def test_liveness_endpoint(client):
    """Verifies that the /live endpoint signals process active status."""
    res = client.get("/live")
    assert res.status_code == 200
    assert res.json() == {"status": "live"}


def test_readiness_endpoint(client):
    """Verifies that the /ready endpoint checks connection pooling readiness."""
    res = client.get("/ready")
    assert res.status_code == 200
    assert res.json() == {"status": "ready"}


def test_health_check_endpoint(client):
    """Verifies that the /health endpoint checks system component stats."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    assert res.json()["database"] == "connected"


def test_version_endpoint(client):
    """Verifies version check metadata format."""
    res = client.get("/version")
    assert res.status_code == 200
    assert "version" in res.json()
    assert "environment" in res.json()


def test_metrics_exporter_endpoint(client):
    """Verifies Prometheus plain text scrapability format."""
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "app_objects_total" in res.text
    assert "# HELP" in res.text
