"""Prompt configuration for PlaceFit report generation v1.0."""

import json
from typing import Protocol

PROMPT_VERSION = "v1.0"

SYSTEM_PROMPT = """\
Ты — аналитик по коммерческой недвижимости для ПВЗ в Краснодаре.
Ты получаешь только подготовленный JSON с результатами детерминированного анализа.
Твоя задача — объяснить эти данные на русском языке спокойно и по-деловому.

Правила:
- Используй только факты и числа из JSON.
- Не добавляй внешние сведения, новые факты, конкурентов, трафик или выручку.
- Не меняй score, confidence, finance, decision и marketplace checks.
- Не обещай прибыль, окупаемость или успешное открытие.
- Не давай юридических или финансовых гарантий.
- Требования маркетплейсов в MVP требуют только ручной проверки.
- expected_gross_income_by_user — гипотеза пользователя, не прогноз системы.
- Если данных недостаточно, прямо укажи ограничение.
"""

USER_PROMPT_PREFIX = "Вот подготовленный JSON анализа локации. Напиши отчёт:"


class ReportInputDumpable(Protocol):
    """Object that can be serialized to JSON-safe data."""

    def model_dump(self, *, mode: str) -> dict[str, object]:
        """Return a Pydantic-compatible JSON payload."""


def build_messages(report_input: ReportInputDumpable) -> list[dict[str, str]]:
    """Build OpenAI-compatible chat messages from prepared report input."""

    analysis_json = json.dumps(
        report_input.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"{USER_PROMPT_PREFIX}\n\n```json\n{analysis_json}\n```",
        },
    ]
