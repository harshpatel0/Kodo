class CacheControl:
    def __init__(self, system_prompt: str) -> None:
        self.system_prompt = system_prompt
        self._chunks: list[str] = []

    def append(self, raw: str) -> None:
        self._chunks.append(raw)

    def raw(self) -> str:
        return "".join(self._chunks)

    def system_block(self) -> list[dict]:
        return [
            {
                "type": "text",
                "text": self.system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]

    def user_content_block(self, user_text: str) -> list[dict]:
        return [
            {"type": "text", "text": user_text, "cache_control": {"type": "ephemeral"}}
        ]
