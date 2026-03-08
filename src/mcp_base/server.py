"""FastMCP server entrypoint for the mcp-filesystem-readonly server.

Run with::

    uv run python -m mcp_base

or via the installed script::

    mcp-base
"""

import argparse
from pathlib import Path
from typing import Any

import fastmcp

from mcp_base.config import FilesystemConfig, load_config
from mcp_base.logging import Logger, make_logger
from mcp_base.tools import health_check as _health_check
from mcp_base.tools import list_folder as _list_folder
from mcp_base.tools import list_inclusion_filters as _list_inclusion_filters
from mcp_base.tools import list_root_paths as _list_root_paths

mcp = fastmcp.FastMCP("mcp-filesystem-readonly")

_logger: Logger | None = None
_filesystem_config: FilesystemConfig | None = None


@mcp.tool()
def health_check() -> dict[str, str]:
    """Return a simple health status indicating the server is running.

    Returns:
        A dict with a single ``status`` key set to ``"ok"``.
    """
    return _health_check()


@mcp.tool()
def list_root_paths() -> list[str]:
    """Return the configured root paths available for filesystem listing.

    Returns:
        The list of absolute paths of the configured root directories.
    """
    return _list_root_paths(_filesystem_config.roots if _filesystem_config else [])


@mcp.tool()
def list_inclusion_filters() -> list[dict[str, Any]]:
    """Return all available inclusion filters for use with list_folder.

    Filters define which file types and folders are included in directory listings.
    Call this first to discover valid filter names, then pass one to list_folder.

    Returns:
        A list of filters, each with a ``name``, ``includes_folders``, and
        ``included_extensions``.
    """
    return _list_inclusion_filters()


@mcp.tool()
def list_folder(path: str, inclusion_filter_name: str) -> list[dict[str, Any]]:
    """List the contents of a directory within the configured roots.

    Args:
        path: Absolute path of the directory to list. Must be within one of the configured roots.
        inclusion_filter_name: Name of the filter to apply. Call list_inclusion_filters first
            to discover valid filter names.

    Returns:
        A list of entries, each with ``name``, ``size_mb``, and ``is_folder``.
    """
    return _list_folder(path, _filesystem_config.roots if _filesystem_config else [], inclusion_filter_name)


def main() -> None:
    """Parse CLI arguments, load configuration, and start the MCP server."""
    parser = argparse.ArgumentParser(description="mcp-filesystem-readonly MCP server")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.toml"),
        help="Path to config.toml (default: config.toml)",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    global _logger, _filesystem_config
    _logger = make_logger(config.logging.level)
    _filesystem_config = config.filesystem

    mcp.run(
        transport="streamable-http",
        host=config.server.host,
        port=config.server.port,
    )
