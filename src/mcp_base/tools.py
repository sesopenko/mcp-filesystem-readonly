"""MCP tool implementations for the mcp-filesystem-readonly server."""

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def health_check() -> dict[str, str]:
    """Return a simple health status indicating the server is running.

    Returns:
        A dict with a single ``status`` key set to ``"ok"``.
    """
    return {"status": "ok"}


def get_root_path(root: str) -> str:
    """Return the configured root path for filesystem access.

    Args:
        root: The configured root directory path.

    Returns:
        The root path string as configured.
    """
    return root


def list_folder(
    path: str,
    root: str,
    folders_only: bool = False,
) -> list[dict[str, Any]]:
    """List the contents of a directory within the configured root.

    Args:
        path: Absolute path of the directory to list. Must be within *root*.
        root: The configured root directory. Entries outside this path are blocked.
        folders_only: When ``True``, only directory entries are returned.

    Returns:
        A list of dicts, each with keys ``name``, ``size_mb``, ``date_created``,
        ``date_modified``, and ``is_folder``. ``size_mb`` is ``0.0`` for directories.

    Raises:
        ValueError: If *path* is relative, or resolves to a location outside *root*.
        FileNotFoundError: If *path* does not exist.
        NotADirectoryError: If *path* is not a directory.
    """
    if not Path(path).is_absolute():
        raise ValueError(f"Path must be absolute, got: {path!r}")

    resolved_path = Path(path).resolve()
    resolved_root = Path(root).resolve()

    if resolved_path != resolved_root and not str(resolved_path).startswith(str(resolved_root) + os.sep):
        raise ValueError(f"Path is outside the configured folder: {path!r}")

    entries: list[dict[str, Any]] = []
    with os.scandir(resolved_path) as it:
        for entry in it:
            stat = entry.stat(follow_symlinks=False)
            is_folder = entry.is_dir(follow_symlinks=False)

            if folders_only and not is_folder:
                continue

            size_mb = 0.0 if is_folder else stat.st_size / (1024 * 1024)
            created_ts = getattr(stat, "st_birthtime", stat.st_ctime)
            date_created = datetime.fromtimestamp(created_ts, tz=UTC).isoformat()
            date_modified = datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat()

            entries.append(
                {
                    "name": entry.name,
                    "size_mb": size_mb,
                    "date_created": date_created,
                    "date_modified": date_modified,
                    "is_folder": is_folder,
                }
            )

    return entries
