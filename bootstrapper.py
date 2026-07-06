"""
The place to put any code that needs to be run first
"""

from utils.logger import logger
import json
from pathlib import Path
from typing import List, Literal

from utils.globals import AVAILABLE_INTERACTION_LAYERS

import mcp.shared.exceptions

CURRENT_DIR = Path(__file__).resolve().parent


def setup_mcps():
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
        try:
            run_async(mcp_registry.register(server["name"], server))
            logger.info(f"Registered MCP server: {server['name']}")
        except mcp.shared.exceptions.McpError as e:
            logger.warning(f"Failed to register {server['name']}, {e}")

    if not mcp_registry.get_tool_schemas():
        logger.debug(f"MCP Registered: {mcp_registry.get_tool_schemas()}")


def check_layers():
    from utils import check_layer

    enabled_layers = 0

    for layer in AVAILABLE_INTERACTION_LAYERS:
        if check_layer(layer):
            enabled_layers += 1

    if enabled_layers == 0:
        print("At least one interaction layer needs to be enabled for Kodo to work")
        exit(1)
