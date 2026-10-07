from pathlib import Path

import pytest

from monitor.config import ConfigError, load_config


VALID_CONFIG = """
monitoring:
  interval_seconds: 10
thresholds:
  cpu: {warning: 75, critical: 90}
  memory: {warning: 80, critical: 95}
  disk: {warning: 80, critical: 90}
network_checks:
  - {name: Web, host: localhost, port: 443}
http_checks:
  - {name: API, url: "https://example.test", expected_status: 200}
process_checks:
  - {name: SSH, process_name: sshd}
"""


def test_load_valid_config(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(VALID_CONFIG, encoding="utf-8")
    config = load_config(path)
    assert config["monitoring"]["interval_seconds"] == 10
    assert config["network_checks"][0]["port"] == 443


@pytest.mark.parametrize(
    "bad_config, message",
    [
        ("thresholds: []", "monitoring"),
        (VALID_CONFIG.replace("warning: 75", "warning: 95"), "warning threshold"),
        (VALID_CONFIG.replace("port: 443", "port: invalid"), "port"),
        ("monitoring: [broken", "Invalid YAML"),
    ],
)
def test_malformed_config_has_useful_error(tmp_path: Path, bad_config: str, message: str) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(bad_config, encoding="utf-8")
    with pytest.raises(ConfigError, match=message):
        load_config(path)


def test_missing_config_has_useful_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "missing.yaml")
