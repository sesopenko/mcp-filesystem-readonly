"""Unit tests for MCP tool implementations."""

from pathlib import Path

import pytest

from mcp_base.tools import health_check, list_folder, list_root_paths


def test_health_check_returns_ok() -> None:
    """health_check returns {"status": "ok"}."""
    result = health_check()
    assert result == {"status": "ok"}


def test_list_root_paths_returns_configured_roots() -> None:
    """list_root_paths returns the list of roots passed in."""
    roots = ["/mnt/video", "/mnt/music"]
    assert list_root_paths(roots) == roots


def test_list_folder_returns_entries(tmp_path: Path) -> None:
    """list_folder returns an entry for each item in the directory."""
    (tmp_path / "file.txt").write_text("hello")
    (tmp_path / "subdir").mkdir()

    result = list_folder(str(tmp_path), [str(tmp_path)])

    names = {e["name"] for e in result}
    assert "file.txt" in names
    assert "subdir" in names


def test_list_folder_folders_only(tmp_path: Path) -> None:
    """list_folder with folders_only=True returns only directory entries."""
    (tmp_path / "file.txt").write_text("hello")
    (tmp_path / "subdir").mkdir()

    result = list_folder(str(tmp_path), [str(tmp_path)], folders_only=True)

    assert all(e["is_folder"] for e in result)
    names = {e["name"] for e in result}
    assert "subdir" in names
    assert "file.txt" not in names


def test_list_folder_entry_fields(tmp_path: Path) -> None:
    """list_folder entries contain the required fields."""
    (tmp_path / "file.txt").write_text("hello")

    result = list_folder(str(tmp_path), [str(tmp_path)])

    assert len(result) == 1
    entry = result[0]
    assert set(entry.keys()) == {"name", "size_mb", "date_created", "date_modified", "is_folder"}


def test_list_folder_entry_name_is_basename(tmp_path: Path) -> None:
    """list_folder entries use the item's basename, not the full path."""
    (tmp_path / "file.txt").write_text("hello")

    result = list_folder(str(tmp_path), [str(tmp_path)])

    assert result[0]["name"] == "file.txt"


def test_list_folder_size_mb(tmp_path: Path) -> None:
    """list_folder reports correct size_mb for files and 0.0 for directories."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"x" * 1024 * 1024)  # exactly 1 MiB
    (tmp_path / "subdir").mkdir()

    result = list_folder(str(tmp_path), [str(tmp_path)])
    by_name = {e["name"]: e for e in result}

    assert by_name["data.bin"]["size_mb"] == pytest.approx(1.0, rel=1e-3)
    assert by_name["subdir"]["size_mb"] == 0.0


def test_list_folder_path_inside_second_root_accepted(tmp_path: Path) -> None:
    """list_folder accepts a path within the second configured root."""
    root1 = tmp_path / "root1"
    root1.mkdir()
    root2 = tmp_path / "root2"
    root2.mkdir()
    (root2 / "file.txt").write_text("hello")

    result = list_folder(str(root2), [str(root1), str(root2)])

    names = {e["name"] for e in result}
    assert "file.txt" in names


def test_list_folder_path_outside_all_roots_raises(tmp_path: Path) -> None:
    """list_folder raises ValueError when path is outside all configured roots."""
    root1 = tmp_path / "root1"
    root1.mkdir()
    root2 = tmp_path / "root2"
    root2.mkdir()
    outside = tmp_path / "other"
    outside.mkdir()

    with pytest.raises(ValueError, match="outside all configured roots"):
        list_folder(str(outside), [str(root1), str(root2)])


def test_list_folder_relative_path_raises(tmp_path: Path) -> None:
    """list_folder raises ValueError for a relative path input."""
    with pytest.raises(ValueError, match="absolute"):
        list_folder("relative/path", [str(tmp_path)])
