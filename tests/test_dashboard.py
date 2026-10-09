from datetime import datetime

from dashboard import create_app
from monitor.health import CheckResult, HealthStatus


def test_dashboard_page_loads() -> None:
    client = create_app("config.yaml").test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Infrastructure overview" in response.data


def test_health_api_returns_monitor_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        "dashboard.collect_checks",
        lambda config, section=None: {
            "system": [CheckResult("CPU Utilization", HealthStatus.HEALTHY, "20.0%")]
        },
    )
    client = create_app("config.yaml").test_client()
    response = client.get("/api/health")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["overall_status"] == "HEALTHY"
    assert payload["sections"]["system"][0]["name"] == "CPU Utilization"


def test_health_api_rejects_unknown_section() -> None:
    client = create_app("config.yaml").test_client()
    response = client.get("/api/health?section=invalid")
    assert response.status_code == 400
    assert "Unknown section" in response.get_json()["error"]
