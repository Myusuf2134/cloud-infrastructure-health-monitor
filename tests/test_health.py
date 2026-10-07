from monitor.health import CheckResult, HealthStatus, classify_threshold, overall_status


def test_threshold_classification() -> None:
    assert classify_threshold(74.9, 75, 90) == HealthStatus.HEALTHY
    assert classify_threshold(75, 75, 90) == HealthStatus.WARNING
    assert classify_threshold(90, 75, 90) == HealthStatus.CRITICAL


def test_overall_health_uses_most_severe_result() -> None:
    results = [
        CheckResult("ok", HealthStatus.HEALTHY, "ok"),
        CheckResult("warn", HealthStatus.WARNING, "warn"),
        CheckResult("critical", HealthStatus.CRITICAL, "critical"),
    ]
    assert overall_status(results) == HealthStatus.CRITICAL
    assert overall_status([]) == HealthStatus.UNKNOWN
