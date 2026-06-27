from dataclasses import dataclass


@dataclass
class PCActionResult:
    command: str = "PROCEED"
    error_message: str = ""
