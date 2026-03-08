"""Unit tests for MCP tool implementations."""

from pathlib import Path

import pytest

from mcp_base.tools import health_check, list_folder, list_inclusion_filters, list_root_paths


def test_health_check_returns_ok() -> None:
    """health_check returns {"status": "ok"}."""
    result = health_check()
    assert result == {"status": "ok"}


def test_list_root_paths_returns_configured_roots() -> None:
    """list_root_paths returns the list of roots passed in."""
    roots = ["/mnt/video", "/mnt/music"]
    assert list_root_paths(roots) == roots


def test_list_inclusion_filters_returns_expected_names() -> None:
    """list_inclusion_filters returns all expected filter names."""
    result = list_inclusion_filters()
    names = {f["name"] for f in result}
    assert names == {"all", "folders_only", "videos", "music", "pictures"}


def test_list_inclusion_filters_schema() -> None:
    """list_inclusion_filters returns dicts with expected keys."""
    result = list_inclusion_filters()
    for f in result:
        assert set(f.keys()) == {"name", "includes_folders", "included_extensions"}
        assert isinstance(f["name"], str)
        assert isinstance(f["includes_folders"], bool)
        assert f["included_extensions"] is None or isinstance(f["included_extensions"], str)


def test_list_folder_filter_all(tmp_path: Path) -> None:
    """list_folder with 'all' filter returns files and folders."""
    (tmp_path / "file.txt").write_text("hello")
    (tmp_path / "subdir").mkdir()

    result = list_folder(str(tmp_path), [str(tmp_path)], "all")

    names = {e["name"] for e in result}
    assert "file.txt" in names
    assert "subdir" in names


def test_list_folder_filter_folders_only(tmp_path: Path) -> None:
    """list_folder with 'folders_only' filter returns only directory entries."""
    (tmp_path / "file.txt").write_text("hello")
    (tmp_path / "subdir").mkdir()

    result = list_folder(str(tmp_path), [str(tmp_path)], "folders_only")

    assert all(e["is_folder"] for e in result)
    names = {e["name"] for e in result}
    assert "subdir" in names
    assert "file.txt" not in names


def test_list_folder_entry_fields(tmp_path: Path) -> None:
    """list_folder entries contain the required fields."""
    (tmp_path / "file.txt").write_text("hello")

    result = list_folder(str(tmp_path), [str(tmp_path)], "all")

    assert len(result) == 1
    entry = result[0]
    assert set(entry.keys()) == {"name", "size_mb", "is_folder"}


def test_list_folder_entry_name_is_basename(tmp_path: Path) -> None:
    """list_folder entries use the item's basename, not the full path."""
    (tmp_path / "file.txt").write_text("hello")

    result = list_folder(str(tmp_path), [str(tmp_path)], "all")

    assert result[0]["name"] == "file.txt"


def test_list_folder_size_mb(tmp_path: Path) -> None:
    """list_folder reports correct size_mb for files and None for directories."""
    f = tmp_path / "data.bin"
    f.write_bytes(b"x" * 1024 * 1024)  # exactly 1 MiB
    (tmp_path / "subdir").mkdir()

    result = list_folder(str(tmp_path), [str(tmp_path)], "all")
    by_name = {e["name"]: e for e in result}

    assert by_name["data.bin"]["size_mb"] == pytest.approx(1.0, rel=1e-3)
    assert by_name["subdir"]["size_mb"] is None


def test_list_folder_path_inside_second_root_accepted(tmp_path: Path) -> None:
    """list_folder accepts a path within the second configured root."""
    root1 = tmp_path / "root1"
    root1.mkdir()
    root2 = tmp_path / "root2"
    root2.mkdir()
    (root2 / "file.txt").write_text("hello")

    result = list_folder(str(root2), [str(root1), str(root2)], "all")

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
        list_folder(str(outside), [str(root1), str(root2)], "all")


def test_list_folder_relative_path_raises(tmp_path: Path) -> None:
    """list_folder raises ValueError for a relative path input."""
    with pytest.raises(ValueError, match="absolute"):
        list_folder("relative/path", [str(tmp_path)], "all")


def test_list_folder_filter_videos(tmp_path: Path) -> None:
    """list_folder with 'videos' filter returns video files and folders."""
    (tmp_path / "movie.mkv").write_text("video")
    (tmp_path / "video.mp4").write_text("video")
    (tmp_path / "metadata.nfo").write_text("nfo")
    (tmp_path / "poster.jpg").write_text("jpg")
    (tmp_path / "subfolder").mkdir()

    result = list_folder(str(tmp_path), [str(tmp_path)], "videos")

    names = {e["name"] for e in result}
    assert "movie.mkv" in names
    assert "video.mp4" in names
    assert "subfolder" in names
    assert "metadata.nfo" not in names
    assert "poster.jpg" not in names


def test_list_folder_filter_videos_case_insensitive(tmp_path: Path) -> None:
    """list_folder filters files case-insensitively."""
    (tmp_path / "movie.MKV").write_text("video")
    (tmp_path / "video.MP4").write_text("video")

    result = list_folder(str(tmp_path), [str(tmp_path)], "videos")

    names = {e["name"] for e in result}
    assert "movie.MKV" in names
    assert "video.MP4" in names


def test_list_folder_filter_music(tmp_path: Path) -> None:
    """list_folder with 'music' filter returns music files and folders."""
    (tmp_path / "song.mp3").write_text("audio")
    (tmp_path / "track.flac").write_text("audio")
    (tmp_path / "metadata.nfo").write_text("nfo")
    (tmp_path / "album_art.jpg").write_text("jpg")
    (tmp_path / "subfolder").mkdir()

    result = list_folder(str(tmp_path), [str(tmp_path)], "music")

    names = {e["name"] for e in result}
    assert "song.mp3" in names
    assert "track.flac" in names
    assert "subfolder" in names
    assert "metadata.nfo" not in names
    assert "album_art.jpg" not in names


def test_list_folder_filter_pictures(tmp_path: Path) -> None:
    """list_folder with 'pictures' filter returns picture files and folders."""
    (tmp_path / "photo.jpg").write_text("image")
    (tmp_path / "screenshot.png").write_text("image")
    (tmp_path / "thumbnail.nfo").write_text("nfo")
    (tmp_path / "subfolder").mkdir()

    result = list_folder(str(tmp_path), [str(tmp_path)], "pictures")

    names = {e["name"] for e in result}
    assert "photo.jpg" in names
    assert "screenshot.png" in names
    assert "subfolder" in names
    assert "thumbnail.nfo" not in names


def test_list_folder_filter_invalid_name_raises(tmp_path: Path) -> None:
    """list_folder raises ValueError for an unknown filter name."""
    with pytest.raises(ValueError, match="Unknown inclusion filter"):
        list_folder(str(tmp_path), [str(tmp_path)], "nonexistent")
