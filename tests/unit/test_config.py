"""Unit tests for config loading."""

import tomllib
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from mcp_base.config import AppConfig, FilesystemConfig, LoggingConfig, ServerConfig, load_config

VALID_TOML = b"""
[server]
host = "0.0.0.0"
port = 8080

[logging]
level = "debug"

[filesystem]
roots = "/tmp/a,/tmp/b"
"""


def test_load_config_returns_correct_types() -> None:
    """load_config returns an AppConfig with correctly typed nested dataclasses."""
    with patch("builtins.open", mock_open(read_data=VALID_TOML)):
        config = load_config(Path("config.toml"))

    assert isinstance(config, AppConfig)
    assert isinstance(config.server, ServerConfig)
    assert isinstance(config.logging, LoggingConfig)
    assert isinstance(config.filesystem, FilesystemConfig)


def test_load_config_server_values() -> None:
    """load_config correctly parses [server] section values."""
    with patch("builtins.open", mock_open(read_data=VALID_TOML)):
        config = load_config(Path("config.toml"))

    assert config.server.host == "0.0.0.0"
    assert config.server.port == 8080


def test_load_config_logging_values() -> None:
    """load_config correctly parses [logging] section values."""
    with patch("builtins.open", mock_open(read_data=VALID_TOML)):
        config = load_config(Path("config.toml"))

    assert config.logging.level == "debug"


def test_load_config_missing_file_raises() -> None:
    """load_config raises FileNotFoundError when the file does not exist."""
    with pytest.raises(FileNotFoundError):
        load_config(Path("/nonexistent/config.toml"))


def test_load_config_missing_section_raises() -> None:
    """load_config raises KeyError when a required section is missing."""
    incomplete = b"""
[server]
host = "localhost"
port = 8080
"""
    with patch("builtins.open", mock_open(read_data=incomplete)):
        with pytest.raises(KeyError):
            load_config(Path("config.toml"))


def test_load_config_invalid_toml_raises() -> None:
    """load_config raises TOMLDecodeError when the file is malformed."""
    with patch("builtins.open", mock_open(read_data=b"not valid toml [[[[")):
        with pytest.raises(tomllib.TOMLDecodeError):
            load_config(Path("config.toml"))


def test_load_config_filesystem_roots() -> None:
    """load_config correctly parses [filesystem] roots as a list."""
    with patch("builtins.open", mock_open(read_data=VALID_TOML)):
        config = load_config(Path("config.toml"))

    assert config.filesystem.roots == ["/tmp/a", "/tmp/b"]


def test_load_config_filesystem_single_root() -> None:
    """load_config parses a single path (no comma) as a one-element list."""
    single = b"""
[server]
host = "0.0.0.0"
port = 8080

[logging]
level = "info"

[filesystem]
roots = "/tmp"
"""
    with patch("builtins.open", mock_open(read_data=single)):
        config = load_config(Path("config.toml"))

    assert config.filesystem.roots == ["/tmp"]


def test_load_config_filesystem_roots_whitespace_trimmed() -> None:
    """load_config strips whitespace from each root path."""
    padded = b"""
[server]
host = "0.0.0.0"
port = 8080

[logging]
level = "info"

[filesystem]
roots = " /tmp/a , /tmp/b "
"""
    with patch("builtins.open", mock_open(read_data=padded)):
        config = load_config(Path("config.toml"))

    assert config.filesystem.roots == ["/tmp/a", "/tmp/b"]


def test_load_config_missing_filesystem_raises() -> None:
    """load_config raises KeyError when [filesystem] section is absent."""
    no_filesystem = b"""
[server]
host = "0.0.0.0"
port = 8080

[logging]
level = "info"
"""
    with patch("builtins.open", mock_open(read_data=no_filesystem)):
        with pytest.raises(KeyError):
            load_config(Path("config.toml"))
