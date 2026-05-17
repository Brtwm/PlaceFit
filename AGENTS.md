# AGENTS.md — инструкции для AI-агентов

## Проект

**PlaceFit** — геоаналитическая система поддержки решений для оценки локаций под ПВЗ.

## Контекст

Перед началом работы читай публичную документацию проекта:

1. `docs/00_overview.md` — обзор продукта.
2. `docs/02_mvp_scope.md` — границы MVP.
3. `docs/03_architecture.md` — архитектура и data flow.
4. `docs/04_data_model.md` — модель данных.
5. `docs/05_api_contract.md` — API-контракт.
6. `docs/06_scoring_model.md` — scoring model.
7. `docs/07_financial_model.md` — financial model.
8. `docs/08_ai_report.md` — AI report и fallback.
9. `docs/09_testing_strategy.md` — стратегия тестирования.
10. `docs/13_coding_plan_for_codex_mvp.md` — план реализации MVP.

`memory-bank/` может существовать локально как рабочая память проекта, но не является обязательным публичным source of truth.

## Ключевые правила

### Архитектура

- **«AI объясняет, код считает»** — scoring, finance, decision и confidence считает только детерминированный backend code.
- LLM получает только подготовленный JSON и генерирует текстовый отчёт.
- LLM не имеет доступа к БД, внешним API, shell или секретам.
- **Provider abstraction** — внешние API должны быть за Protocol-интерфейсами.
- **Scoring versioning в MVP** — правила хранятся в БД, каждый анализ привязан к `scoring_version_id`.

### MVP scope

- Только ПВЗ (`business_type = "pvz"`).
- Только Краснодар.
- Только анализ конкретного адреса.
- Streamlit UI + FastAPI backend + PostgreSQL/PostGIS.
- Не начинать реализацию backend/frontend, если пользователь явно просит только документацию или подготовку репозитория.

### Запрещено в MVP

- ML-модели для прогноза.
- H3/heatmap/city-wide search.
- Trendwatcher.
- Browser-agent.
- Парсинг Авито/Циан.
- Telegram-бот.
- Авторизация и multi-user режим.
- Хардкодить иллюстративные требования маркетплейсов как юридически/операционно точные правила.

### Документация и примеры

- Примеры должны быть детерминированными и пригодными для тестов.
- Если меняются веса scoring/confidence, обновляй API examples, AI report examples и developer TZ синхронно.
- Если основной AI provider недоступен, template report возвращается как успешный response с `report.status = "fallback"`.
- Top-level `LLM_FAILED` допустим только если отчёт не удалось создать вообще.

### Безопасность

- API ключи только в `.env`.
- Не передавать ключи на frontend.
- Не коммитить реальные секреты.
- Не выдавать отчёт как финансовую гарантию.

### Стиль будущего кода

- Python 3.11+.
- Type hints обязательны.
- Pydantic v2 для валидации.
- SQLAlchemy 2.x.
- pytest для тестов.
- structlog или loguru для логирования.
