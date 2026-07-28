"""Exponential backoff with jitter."""

import random


def compute_delay(attempt: int, base: float = 1.0, cap: float = 30.0) -> float:
    """Delay before the next retry.

    attempt 1 -> ~1s, attempt 2 -> ~2s, attempt 3 -> ~4s ... capped at `cap`.
    A random jitter (0-25%) is added so many simultaneous failures don't all
    retry at the exact same instant (the 'thundering herd' problem).
    """
    exponential = min(base * (2 ** (attempt - 1)), cap)
    jitter = exponential * random.uniform(0, 0.25)
    return exponential + jitter
