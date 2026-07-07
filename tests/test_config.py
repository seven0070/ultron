"""Tests for Build #003 — ConfigManager."""

from pathlib import Path

import pytest

from monad.config import ConfigError, ConfigManager


def _write_config(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def test_load_valid_config(tmp_path):
    p = _write_config(tmp_path, """
application: {name: test, version: 0.1}
paths: {models_dir: models}
runtime: {default_engine: llama_cpp}
logging: {level: INFO}
""")
    cm = ConfigManager(p)
    cm.load()
    assert cm.get("application.name") == "test"
    assert cm.get("logging.level") == "INFO"
    assert cm.get("missing.key", "default") == "default"


def test_missing_file(tmp_path):
    with pytest.raises(ConfigError):
        ConfigManager(tmp_path / "nope.yaml").load()


def test_missing_section(tmp_path):
    p = _write_config(tmp_path, "application: {name: test}\n")
    with pytest.raises(ConfigError):
        ConfigManager(p).load()


def test_invalid_yaml(tmp_path):
    p = _write_config(tmp_path, "not: [valid: yaml")
    with pytest.raises(ConfigError):
        ConfigManager(p).load()
