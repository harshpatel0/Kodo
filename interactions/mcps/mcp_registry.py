from interactions.mcps.mcp_client import MCPClient
from utils.logger import logger


class MCPRegistry:
    def __init__(self):
        self._clients: dict[str, MCPClient] = {}
        self._tools: dict[str, tuple[str, any]] = {}
        # tool_name -> (server_name, tool_def), and thats what it looks like

    async def register(self, name: str, config: dict):
        client = MCPClient(config)
        await client.connect()
        self._clients[name] = client
        for tool in await client.list_tools():
            self._tools[tool.name] = (name, tool)

    async def call(self, tool_name: str, arguments: dict):
        logger.info(f"Calling {tool_name} with arguments: {arguments}")
        server_name, _ = self._tools[tool_name]
        return await self._clients[server_name].call_tool(tool_name, arguments)

    def check_tool(self, tool_name: str) -> bool:
        tool_exists = tool_name in self._tools

        if not tool_exists:
            logger.warning(f"The LLM called a non existent tool: {tool_name}")

        return tool_exists

    def get_tool_schemas(self) -> str:
        if not self._tools:
            return ""
        lines = []
        for tool_name, (server_name, tool) in self._tools.items():
            lines.append(f"### [{server_name}] {tool_name}")
            if tool.description:
                lines.append(f"Description: {tool.description}")
            if tool.inputSchema:
                props = tool.inputSchema.get("properties", {})
                required = tool.inputSchema.get("required", [])
                if props:
                    lines.append("Arguments:")
                    for arg_name, arg_schema in props.items():
                        req = " (required)" if arg_name in required else ""
                        arg_type = arg_schema.get("type", "any")
                        arg_desc = arg_schema.get("description", "")
                        lines.append(f"  - {arg_name} ({arg_type}){req}: {arg_desc}")
            lines.append("")
        return "\n".join(lines).strip()


mcp_registry = MCPRegistry()
