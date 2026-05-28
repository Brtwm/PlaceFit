from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_env_example_keeps_real_provider_keys_empty() -> None:
    env_text = (ROOT / ".env.example").read_text(encoding="utf-8")

    assert "DGIS_API_KEY=\n" in env_text
    assert "LLM_API_KEY=\n" in env_text
    assert "LLM_ENABLED=false" in env_text
    assert "GEOCODER_PROVIDER=fake" in env_text
    assert "POI_PROVIDER=fake" in env_text


def test_env_example_does_not_contain_obvious_real_secrets() -> None:
    env_text = (ROOT / ".env.example").read_text(encoding="utf-8").lower()
    forbidden_fragments = [
        "sk-",
        "api_key_here",
        "your_api_key",
        "replace_me",
        "changeme",
        "secret=",
        "token=",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in env_text


def test_compose_declares_required_services() -> None:
    compose_text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "\n  db:\n" in compose_text
    assert "\n  backend:\n" in compose_text
    assert "\n  streamlit:\n" in compose_text


def test_compose_has_healthchecks_and_expected_ports() -> None:
    compose_text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert compose_text.count("healthcheck:") >= 3
    assert 'condition: service_healthy' in compose_text
    assert '"5432:5432"' in compose_text
    assert '"8000:8000"' in compose_text
    assert '"8501:8501"' in compose_text
    assert "http://backend:8000/api/v1" in compose_text
