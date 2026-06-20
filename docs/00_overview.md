# PlaceFit — обзор продукта

## Что это

**PlaceFit** — геоаналитическая система поддержки решений для оценки одной
коммерческой локации под ПВЗ и сравнения 2-5 кандидатных локаций. MVP / V1.0
сфокусирован на анализе конкретного адреса в Краснодаре.

Текущий статус: **V1.3 Markdown-only export/reporting polish implemented and
accepted locally**.
Backend, PostgreSQL/PostGIS, deterministic services, fake/fallback providers,
optional real providers, AI/fallback report, Streamlit UI, карта, чек-лист,
история анализов, compare mode и snapshot-only Markdown downloads для нового
анализа, сохранённой detail page и compare result уже реализованы. CSV, Excel,
PDF и public export API endpoints отложены.

## Целевой пользователь

Предприниматель, менеджер по развитию или аналитик, который выбирает помещение
под ПВЗ и хочет быстро получить предварительную, воспроизводимую оценку.

## Ключевая ценность

| Проблема | Решение PlaceFit |
|---|---|
| Конкурентов приходится вручную искать на картах | Поиск и дедупликация POI в радиусах 300/500/700 м |
| Финансовая оценка живёт в Excel или "в голове" | Детерминированная модель costs, break-even, payback |
| Трудно сравнить качество локации | Rule-based score 0-100 с компонентами |
| Неясно, насколько оценке можно доверять | Отдельный confidence score |
| Отчёт может звучать слишком уверенно | AI/fallback report объясняет только готовый JSON |

## MVP / V1.0 scope

- Один город: Краснодар.
- Один бизнес-тип: PVZ / ПВЗ (`business_type = "pvz"`).
- Один сценарий: анализ конкретного адреса.
- Результат: score, confidence, finance, decision, report, checklist, map,
  history.
- Demo path работает без внешних API keys и без LLM key.

## Принцип работы

```text
Address + inputs
  -> geocoding
  -> competitors + deduplication
  -> deterministic scoring / finance / confidence / decision
  -> AI report or fallback report
  -> saved analysis + UI result
```

**AI explains, deterministic code decides.** LLM не является источником фактов,
не считает score, confidence, finance или decision и не имеет доступа к БД,
shell, external APIs или секретам.

## Краткий roadmap

- **V1.1**: stabilization, manual validation, docs hardening.
- **V1.2**: compare mode for 2-5 newly entered candidate locations and
  Markdown compare export.
- **V1.3**: Markdown-only Streamlit downloads from existing analysis/detail and
  compare snapshots are implemented; CSV/PDF/Excel and public export APIs are
  deferred.
- **V1.4**: manual refresh and delta view for saved locations.
- **V1.5**: scoring governance and source-tracked marketplace rule maturity.
- **V2**: city-wide location intelligence for PVZ only.
- **V3**: ML/B2B/multi-business platform after dataset/backtesting.

Полный roadmap: [docs/10_roadmap.md](10_roadmap.md).

Telegram bot is not a product priority. It may be considered only as a thin
wrapper over a mature product if a real customer explicitly requests it.
