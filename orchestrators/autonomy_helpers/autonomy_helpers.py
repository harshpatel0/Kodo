from utils import estimate_tokens


def truncate_data_list(item: list[str], max_tokens=400) -> list[str]:
    if estimate_tokens("\n".join(item)) <= max_tokens:
        return item

    trimmed = []

    for entry in reversed(item):
        candidate = "\n".join([entry] + trimmed)
        if estimate_tokens(candidate) > max_tokens:
            break
        trimmed.insert(0, entry)
    return trimmed


class History:
    def __init__(self) -> None:
        self.history: list[str] = []

    def __str__(self) -> str:
        history_list = truncate_data_list(self.history)
        return "\n".join(history_list)

    def append(self, text: str) -> None:
        self.history.append(text)


class Directive:
    def __init__(self) -> None:
        self.directive: list[str] = []

    def __str__(self) -> str:
        directive_list = truncate_data_list(self.directive)
        return "\n".join(directive_list)

    def append(self, text: str) -> None:
        self.directive.append(text)
