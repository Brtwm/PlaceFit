import socket
from typing import Any

import pytest
from app.config.settings import Settings
from app.providers.factory import build_geocoder_provider, build_poi_providers
from app.providers.geocoder.dgis import DgisGeocoder
from app.providers.geocoder.fake import FakeGeocoder
from app.providers.poi_search.dgis import DgisPoiSearchProvider
from app.providers.poi_search.fake import FakePoiSearchProvider
from app.providers.poi_search.osm import OsmPoiSearchProvider


def settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)


def test_default_settings_return_fake_providers() -> None:
    geocoder = build_geocoder_provider(settings())
    poi_providers = build_poi_providers(settings())

    assert isinstance(geocoder, FakeGeocoder)
    assert len(poi_providers) == 1
    assert isinstance(poi_providers[0], FakePoiSearchProvider)


def test_dgis_geocoder_without_key_falls_back_to_fake() -> None:
    provider = build_geocoder_provider(settings(geocoder_provider="dgis"))

    assert isinstance(provider, FakeGeocoder)


def test_dgis_poi_without_key_falls_back_to_fake() -> None:
    providers = build_poi_providers(settings(poi_provider="dgis"))

    assert len(providers) == 1
    assert isinstance(providers[0], FakePoiSearchProvider)


def test_dgis_geocoder_with_key_returns_real_provider() -> None:
    provider = build_geocoder_provider(
        settings(geocoder_provider="dgis", dgis_api_key="test-key"),
    )

    assert isinstance(provider, DgisGeocoder)


def test_dgis_poi_with_key_returns_real_provider() -> None:
    providers = build_poi_providers(
        settings(poi_provider="dgis", dgis_api_key="test-key"),
    )

    assert len(providers) == 1
    assert isinstance(providers[0], DgisPoiSearchProvider)


def test_osm_poi_provider_returns_overpass_provider() -> None:
    providers = build_poi_providers(settings(poi_provider="osm"))

    assert len(providers) == 1
    assert isinstance(providers[0], OsmPoiSearchProvider)


def test_unknown_provider_names_raise_clear_errors() -> None:
    with pytest.raises(ValueError, match="Unsupported geocoder provider"):
        build_geocoder_provider(settings(geocoder_provider="unknown"))

    with pytest.raises(ValueError, match="Unsupported POI provider"):
        build_poi_providers(settings(poi_provider="unknown"))


def test_factory_construction_does_not_call_network(monkeypatch: Any) -> None:
    def fail_network(*args: object, **kwargs: object) -> None:
        msg = "network calls are not allowed while constructing providers"
        raise AssertionError(msg)

    monkeypatch.setattr(socket, "create_connection", fail_network)

    build_geocoder_provider(
        settings(geocoder_provider="dgis", dgis_api_key="test-key"),
    )
    build_poi_providers(settings(poi_provider="dgis", dgis_api_key="test-key"))
    build_poi_providers(settings(poi_provider="osm"))
