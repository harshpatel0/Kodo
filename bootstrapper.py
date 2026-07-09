"""
The place to put any code that needs to be run first
"""

from utils.logger import logger
import json
from pathlib import Path
from typing import List, Literal

from utils.globals import AVAILABLE_INTERACTION_LAYERS

import mcp.shared.exceptions
from utils import toaster

CURRENT_DIR = Path(__file__).resolve().parent


def setup_mcps():
    toaster.update("Registering MCPs", "Preparing to register MCP Servers")
    from interactions.mcps.mcp_registry import mcp_registry
    from interactions.mcps.mcp_loop import run_async

    config_path = CURRENT_DIR / "mcp_servers.json"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            mcp_config = json.load(f)
    except FileNotFoundError:
        return

    for server in mcp_config["servers"]:
        logger.info(f"Registering MCP server: {server['name']}")
        toaster.update("Registering MCPs", f"Registering {server['name']}")

        try:
            run_async(mcp_registry.register(server["name"], server))

            logger.info(f"Registered MCP server: {server['name']}")
            toaster.update("Registered MCPs", f"Registered {server['name']}")

        except mcp.shared.exceptions.McpError as e:
            logger.warning(f"Failed to register {server['name']}, {e}")

            toaster.update(
                "Registering MCPs", f"Failed to register {server['name']} MCP"
            )

    if not mcp_registry.get_tool_schemas():
        logger.debug(f"MCP Registered: {mcp_registry.get_tool_schemas()}")


def run_config_guard():
    from utils import config_guard

    config_guard()
