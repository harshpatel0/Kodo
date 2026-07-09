from abc import ABC, abstractmethod
from dataclasses import dataclass
from dotenv import load_dotenv

from utils.runtime_globals import CURRENT_MODE

load_dotenv()


def determine_caching(setting_state: bool) -> bool:
    """Disable caching if the mode is not ACTOR or AUTONOMY, as cache invalidation
    penalties will apply if planner or skill_installation mode prompts are cached
    for some providers.
    """
    if setting_state and CURRENT_MODE in ("ACTOR", "AUTONOMY"):
        return True
    return False


@dataclass
class ChatMessage:
    role: str
    content: str
    images: list[str] | None = None


@dataclass
class ChatResponse:
    content: str
    thinking: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_duration_ms: float = 0.0
    load_duration_ms: float = 0.0


class ModelProvider(ABC):
    use_caching: bool = False

    @abstractmethod
    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatResponse:
        raise NotImplementedError
