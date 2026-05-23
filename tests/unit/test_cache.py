from app.services.cache import InMemoryCache, normalize_cache_key


def test_cache_hit_and_miss() -> None:
    cache: InMemoryCache[str, int] = InMemoryCache()

    assert cache.get("missing") is None

    cache.set("answer", 42)

    assert cache.get("answer") == 42


def test_cache_clear_invalidates_entries() -> None:
    cache: InMemoryCache[str, str] = InMemoryCache()
    cache.set("key", "value")

    cache.clear()

    assert cache.get("key") is None


def test_cache_ttl_expiration_uses_injected_clock() -> None:
    now = 100.0

    def clock() -> float:
        return now

    cache: InMemoryCache[str, str] = InMemoryCache(clock=clock)
    cache.set("key", "value", ttl_seconds=10)

    assert cache.get("key") == "value"

    now = 111.0

    assert cache.get("key") is None


def test_normalize_cache_key_is_stable() -> None:
    assert (
        normalize_cache_key(" Geocode ", "Краснодар,  Ул. Красная, 1")
        == "geocode|краснодар, ул. красная, 1"
    )
