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
from mcp_base.tools import get_root_path as _get_root_path
from mcp_base.tools import health_check as _health_check
from mcp_base.tools import list_folder as _list_folder

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
def get_root_path() -> str:
    """Return the configured root path available for filesystem listing.

    Returns:
        The absolute path of the configured root directory.
    """
    return _get_root_path(_filesystem_config.root if _filesystem_config else "")


@mcp.tool()
def list_folder(path: str, folders_only: bool = False) -> list[dict[str, Any]]:
    """List the contents of a directory within the configured root.

    Args:
        path: Absolute path of the directory to list. Must be within the configured root.
        folders_only: When ``True``, only directory entries are returned.

    Returns:
        A list of entries, each with ``name``, ``size_mb``, ``date_created``,
        ``date_modified``, and ``is_folder``.
    """
    return _list_folder(path, _filesystem_config.root if _filesystem_config else "", folders_only)


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
