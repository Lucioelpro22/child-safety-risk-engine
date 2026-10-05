"""Resource limits shared by the HTTP adapter and the deterministic engine."""

from collections.abc import Sequence

MAX_MESSAGE_CHARS = 10_000
MAX_MESSAGES = 100
MAX_TOTAL_CHARS = 100_000


def conversation_text_length(messages: Sequence[str]) -> int:
    """Count the evaluated text, including the newline between messages."""
    return sum(len(message) for message in messages) + max(0, len(messages) - 1)
