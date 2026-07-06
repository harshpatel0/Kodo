from mcp.types import CallToolResult, TextContent


class KodoCallToolResult(CallToolResult):
    def __str__(self) -> str:
        parts = []
        for block in self.content:
            if isinstance(block, TextContent):
                parts.append(block.text)
            else:
                parts.append(f"[{block.type} content]")
        text = "\n".join(parts)
        if self.isError:
            return f"[Error] {text}" if text else "[Error]"
        return text if text else "[Empty result]"
