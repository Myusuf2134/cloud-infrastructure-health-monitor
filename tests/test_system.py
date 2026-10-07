from types import SimpleNamespace

from monitor.health import HealthStatus
from monitor.system import check_cpu, check_disk, check_memory


LIMITS = {"warning": 75, "critical": 90}


def test_cpu_status_logic(monkeypatch) -> None:
    monkeypatch.setattr("monitor.system.psutil.cpu_percent", lambda interval: 76.0)
    assert check_cpu(LIMITS).status == HealthStatus.WARNING


def test_memory_status_logic(monkeypatch) -> None:
    memory = SimpleNamespace(percent=96.0, available=2 * 1024**3)
    monkeypatch.setattr("monitor.system.psutil.virtual_memory", lambda: memory)
    result = check_memory({"warning": 80, "critical": 95})
    assert result.status == HealthStatus.CRITICAL
    assert result.details["available_gib"] == 2.0


def test_disk_status_logic(monkeypatch) -> None:
    disk = SimpleNamespace(percent=20.0, free=50 * 1024**3)
    monkeypatch.setattr("monitor.system.psutil.disk_usage", lambda path: disk)
    result = check_disk(LIMITS)
    assert result.status == HealthStatus.HEALTHY
    assert result.details["available_gib"] == 50.0
