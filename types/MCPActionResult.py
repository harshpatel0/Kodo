from dataclasses import dataclass


@dataclass
class MCPActionResult:
    output: list[str]
    is_error: bool
