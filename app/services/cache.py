"""Typed in-memory cache for offline provider responses."""

from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic
from typing import Generic, TypeVar

K = TypeVar("K", bound=str)
V = TypeVar("V")


@dataclass(frozen=True)
class _CacheEntry(Generic[V]):
    value: V
    expires_at: float | None


class InMemoryCache(Generic[K, V]):
    """Small deterministic cache with optional TTL and injectable clock."""

    def __init__(self, *, clock: Callable[[], float] = monotonic) -> None:
        self._clock = clock
        self._items: dict[K, _CacheEntry[V]] = {}

    def get(self, key: K) -> V | None:
        """Return cached value when present and not expired."""

        entry = self._items.get(key)
        if entry is None:
            return None
        if entry.expires_at is not None and entry.expires_at <= self._clock():
            del self._items[key]
            return None
        return entry.value

    def set(self, key: K, value: V, *, ttl_seconds: float | None = None) -> None:
        """Store a value with optional TTL."""

        expires_at = None
        if ttl_seconds is not None:
            expires_at = self._clock() + ttl_seconds
        self._items[key] = _CacheEntry(value=value, expires_at=expires_at)

    def clear(self) -> None:
        """Remove all entries."""

        self._items.clear()


def normalize_cache_key(*parts: object) -> str:
    """Build a stable, lower-cased key from non-secret input parts."""

    return "|".join(" ".join(str(part).casefold().split()) for part in parts)
