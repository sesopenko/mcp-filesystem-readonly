"""MCP tool implementations for the mcp-filesystem-readonly server."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class InclusionFilter:
    """Defines what file types and folders to include when listing a directory."""

    name: str
    includes_folders: bool
    included_extensions: str | None


_INCLUSION_FILTERS: list[InclusionFilter] = [
    InclusionFilter("all", includes_folders=True, included_extensions="*"),
    InclusionFilter("folders_only", includes_folders=True, included_extensions=None),
    InclusionFilter(
        "videos",
        includes_folders=True,
        included_extensions="mkv, mp4, avi, m4v, mov, wmv, webm, m2ts, mts, ts, vob",
    ),
    InclusionFilter(
        "music",
        includes_folders=True,
        included_extensions="mp3, flac, m4a, aac, wav, ogg, opus, wma, aiff, aif, alac",
    ),
    InclusionFilter(
        "pictures",
        includes_folders=True,
        included_extensions="jpg, jpeg, png, webp, avif, heic, heif, gif, tif, tiff, bmp, svg",
    ),
]


def health_check() -> dict[str, str]:
    """Return a simple health status indicating the server is running.

    Returns:
        A dict with a single ``status`` key set to ``"ok"``.
    """
    return {"status": "ok"}


def list_root_paths(roots: list[str]) -> list[str]:
    """Return the configured root paths for filesystem access.

    Args:
        roots: The list of configured root directory paths.

    Returns:
        The list of root path strings as configured.
    """
    return roots


def list_inclusion_filters() -> list[dict[str, Any]]:
    """Return all available inclusion filters for use with list_folder.

    Filters define which file types and folders are included in directory listings.
    Call this before calling list_folder to discover valid filter names.

    Returns:
        A list of dicts, each with keys ``name``, ``includes_folders``, and
        ``included_extensions``. The ``name`` can be passed to list_folder as the
        ``inclusion_filter_name`` parameter.
    """
    return [
        {
            "name": f.name,
            "includes_folders": f.includes_folders,
            "included_extensions": f.included_extensions,
        }
        for f in _INCLUSION_FILTERS
    ]


def list_folder(
    path: str,
    roots: list[str],
    inclusion_filter_name: str,
) -> list[dict[str, Any]]:
    """List the contents of a directory within the configured roots.

    Args:
        path: Absolute path of the directory to list. Must be within one of *roots*.
        roots: The configured root directories. Entries outside all of these paths are blocked.
        inclusion_filter_name: Name of the filter to apply. Call list_inclusion_filters to
            discover valid filter names. Must be one of the names returned by that function.

    Returns:
        A list of dicts, each with keys ``name``, ``size_mb``, and ``is_folder``.
        ``size_mb`` is ``None`` for directories and rounded to 2 decimal places for files.

    Raises:
        ValueError: If *path* is relative, resolves outside all configured roots, or
            *inclusion_filter_name* is not a valid filter name.
        FileNotFoundError: If *path* does not exist.
        NotADirectoryError: If *path* is not a directory.
    """
    if not Path(path).is_absolute():
        raise ValueError(f"Path must be absolute, got: {path!r}")

    resolved_path = Path(path).resolve()
    for root in roots:
        resolved_root = Path(root).resolve()
        if resolved_path == resolved_root or str(resolved_path).startswith(str(resolved_root) + os.sep):
            break
    else:
        raise ValueError(f"Path is outside all configured roots: {path!r}")

    # Lookup and validate filter
    filter_obj = None
    for f in _INCLUSION_FILTERS:
        if f.name == inclusion_filter_name:
            filter_obj = f
            break

    if filter_obj is None:
        valid_names = ", ".join(f.name for f in _INCLUSION_FILTERS)
        raise ValueError(f"Unknown inclusion filter {inclusion_filter_name!r}. Valid filter names: {valid_names}")

    # Parse included extensions
    include_all_files = filter_obj.included_extensions == "*"
    included_exts: set[str] = set()
    if not include_all_files and filter_obj.included_extensions is not None:
        included_exts = {ext.strip().lower() for ext in filter_obj.included_extensions.split(",")}

    entries: list[dict[str, Any]] = []
    with os.scandir(resolved_path) as it:
        for entry in it:
            stat = entry.stat(follow_symlinks=False)
            is_folder = entry.is_dir(follow_symlinks=False)

            # Filter folders
            if is_folder:
                if not filter_obj.includes_folders:
                    continue
            else:
                # Filter files by extension
                if not include_all_files:
                    if not included_exts:
                        # No extensions allowed (e.g., folders_only filter)
                        continue
                    # Get file extension without the dot, lowercased
                    file_ext = entry.name.rsplit(".", 1)[-1].lower() if "." in entry.name else ""
                    if file_ext not in included_exts:
                        continue

            size_mb = None if is_folder else round(stat.st_size / (1024 * 1024), 2)

            entries.append(
                {
                    "name": entry.name,
                    "size_mb": size_mb,
                    "is_folder": is_folder,
                }
            )

    return entries
