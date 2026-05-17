# PlaceFit MVP Execution Roadmap

## Цель MVP

PlaceFit MVP — рабочий сервис для оценки одного конкретного адреса в Краснодаре под ПВЗ. Пользователь вводит адрес, параметры помещения и финансовые гипотезы; backend детерминированно считает конкурентов, score, confidence, finance и decision; LLM, если включён, только объясняет готовый JSON. Fallback report должен работать без LLM API key.

## Non-goals MVP

- ML-прогноз выручки.
- Авторизация и multi-user режим.
- Telegram-бот.
- H3, heatmap, city-wide search.
- Trendwatcher.
- Browser-agent.
- Парсинг Авито/Циан.
- Автоматический `passed` / `failed` по требованиям маркетплейсов.
- Реальные внешние API как обязательное условие прохождения tests/CI.

## Staged Implementation Phases

### Фаза 0. Repository/bootstrap setup

| Поле | План |
|---|---|
| Цель | Подготовить Python-проект без бизнес-логики. |
| Файлы | `pyproject.toml`, `app/__init__.py`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/fixtures/`. |
| Тесты | Import smoke test. |
| Команды | `pytest`, `ruff check .`, `mypy app`. |
| Acceptance criteria | Все команды проходят; нет DB, API endpoints, providers, UI. |

### Фаза 1. FastAPI skeleton, healthcheck, settings

| Поле | План |
|---|---|
| Цель | Минимальный backend process с `/health` и typed settings. |
| Файлы | `app/main.py`, `app/config/settings.py`, `app/api/v1/router.py`, `tests/unit/test_settings.py`, `tests/integration/test_health.py`. |
| Тесты | Settings defaults; healthcheck 200. |
| Команды | `pytest tests/unit/test_settings.py tests/integration/test_health.py -v`, `ruff check .`, `mypy app`. |
| Acceptance criteria | `uvicorn app.main:app` стартует; LLM выключен по умолчанию; API key не нужен. |

### Фаза 2. Pydantic v2 schemas

| Поле | План |
|---|---|
| Цель | Зафиксировать API contract из `docs/05_api_contract.md`. |
| Файлы | `app/schemas/*.py`, `tests/unit/test_schemas.py`, `tests/fixtures/api/`. |
| Тесты | Request/response examples validate; unsupported business type rejected. |
| Команды | `pytest tests/unit/test_schemas.py -v`, `ruff check app tests`, `mypy app`. |
| Acceptance criteria | `marketplace_requirements` содержит только `ozon`, `wildberries`, `yandex_market`; `ReportResult.provider` поддерживает `openai_compatible` и `fallback`. |

### Фаза 3. Deterministic core без DB

| Поле | План |
|---|---|
| Цель | Реализовать scoring, finance, confidence, decision как pure functions/services. |
| Файлы | `app/services/scoring.py`, `finance.py`, `confidence.py`, `decision.py`, `app/config/scoring_rules.py`, `tests/unit/test_*`. |
| Тесты | Cases из `docs/09_testing_strategy.md`, диапазон score 0-100, детерминизм. |
| Команды | `pytest tests/unit/test_scoring.py tests/unit/test_finance.py tests/unit/test_confidence.py tests/unit/test_decision.py -v`. |
| Acceptance criteria | Default finance даёт `monthly_costs=295000`; `score=82` и profit > 0 дают `можно рассматривать`; нет DB/provider/LLM imports. |

### Фаза 4. Database layer, Alembic, scoring seed

| Поле | План |
|---|---|
| Цель | Persistence layer и active `scoring_versions` для `pvz/v1.0`. |
| Файлы | `app/db/*`, `app/models/*`, `alembic/*`, `tests/integration/test_db_migrations.py`. |
| Тесты | Migration from zero; PostGIS extension; active scoring version exists. |
| Команды | `alembic upgrade head`, `pytest tests/integration/test_db_migrations.py -v`. |
| Acceptance criteria | Fresh DB создаёт MVP tables; `scores.scoring_version_id` ссылается на `scoring_versions`; `trend_score` не входит в MVP schema. |

### Фаза 5. Mocked providers, fixtures, cache, dedup

| Поле | План |
|---|---|
| Цель | Стабилизировать внешние контракты без реальных API. |
| Файлы | `app/providers/geocoder/base.py`, `app/providers/geocoder/fake.py`, `app/providers/poi_search/base.py`, `app/providers/poi_search/fake.py`, `app/services/geocoding.py`, `app/services/competitors.py`, `app/services/cache.py`, `tests/fixtures/`. |
| Тесты | 2GIS fixture parse; mocked Yandex fallback; OSM POI fixture; dedup; city validation. |
| Команды | `pytest tests/unit/test_deduplication.py tests/unit/test_geocoding_parser.py -v`, `pytest -v --tb=short`. |
| Acceptance criteria | Обычные tests не делают network calls; ambiguous address returns suggestions; real Yandex не блокирует MVP. |

### Фаза 6. API endpoints and analysis orchestration

| Поле | План |
|---|---|
| Цель | Полный backend pipeline на mocked providers. |
| Файлы | `app/services/analysis.py`, `app/services/marketplace.py`, `app/api/v1/endpoints/*.py`, `app/api/v1/deps.py`, `tests/integration/test_analyze.py`, `tests/integration/test_locations.py`. |
| Тесты | Analyze success/failures; save to DB; list/detail history; validation errors. |
| Команды | `pytest tests/integration/test_analyze.py tests/integration/test_locations.py -v`, `pytest -v --tb=short`. |
| Acceptance criteria | `POST /api/v1/analyze` возвращает full response; marketplace statuses только `needs_manual_check`; history/detail доступны. |

### Фаза 7. Fallback-first AI report

| Поле | План |
|---|---|
| Цель | Отчёт без LLM и optional OpenAI-compatible provider. |
| Файлы | `app/providers/llm/base.py`, `app/providers/llm/openai_compatible.py`, `app/providers/llm/fallback.py`, `app/services/report.py`, `app/config/prompts/v1_0.py`, `tests/unit/test_report_*`, `tests/fixtures/llm/`. |
| Тесты | Fallback without key; OpenAI-compatible mock success/error; `LLM_FAILED` only when fallback also fails. |
| Команды | `pytest tests/unit/test_report_fallback.py tests/unit/test_report_schema.py -v`, `pytest tests/integration/test_analyze.py -v`. |
| Acceptance criteria | LLM получает только prepared analysis JSON; `LLM_ENABLED=false` -> `report.status=fallback`; no DB/API/shell/secrets access for LLM. |

### Фаза 8. Optional real providers behind settings

| Поле | План |
|---|---|
| Цель | Подключить real providers как optional runtime layer. |
| Файлы | `app/providers/geocoder/dgis.py`, `app/providers/poi_search/dgis.py`, `app/providers/poi_search/osm.py`, `app/providers/factory.py`, `tests/unit/test_provider_factories.py`, `tests/external/`. |
| Тесты | Factory tests; parser tests on fixtures; manual external tests only. |
| Команды | `pytest tests/unit/test_provider_factories.py -v`, `pytest -v --tb=short`, `pytest -m external`. |
| Acceptance criteria | Без API keys приложение работает на mocked/fallback path; real 2GIS optional; real Yandex не блокирует MVP; обычный `pytest` не вызывает внешние API. |

### Фаза 9. Streamlit UI with streamlit-folium

| Поле | План |
|---|---|
| Цель | Полный пользовательский flow поверх backend API. |
| Файлы | `ui/streamlit_app.py`, `ui/pages/analyze.py`, `ui/pages/history.py`, `ui/pages/detail.py`, `ui/components/map.py`, `ui/components/score_card.py`. |
| Зависимости | Добавляются только в этой фазе: `streamlit`, `folium`, `streamlit-folium`. |
| Тесты | Manual UI smoke; backend integration tests остаются safety net. |
| Команды | `streamlit run ui/streamlit_app.py`, `pytest -v --tb=short`. |
| Acceptance criteria | Form отправляет `/analyze`; result показывает score/finance/report/checklist; map показывает location marker и POI markers; popup содержит бренд, тип точки, расстояние; history/detail работают. |

### Фаза 10. Docker Compose, README quickstart, portfolio polish

| Поле | План |
|---|---|
| Цель | Сделать проект запускаемым и презентабельным. |
| Файлы | `Dockerfile`, `docker-compose.yml`, `README.md`, optional demo seed. |
| Тесты | Fresh clone path; no real secrets; service health checks. |
| Команды | `docker compose up --build`, `docker compose exec backend pytest -v --tb=short`. |
| Acceptance criteria | Backend, DB и Streamlit стартуют; migrations apply; README explains env and ports; fallback/demo path не требует real LLM key. |

### Фаза 11. Final verification

| Поле | План |
|---|---|
| Цель | Проверить MVP readiness без добавления новых фич. |
| Команды | `pytest -v --tb=short`, `ruff check .`, `mypy app`, `alembic upgrade head`, `docker compose up --build`. |
| Acceptance criteria | Все проверки проходят; ограничения MVP соблюдены; GitHub presentation готов к демонстрации. |

## Codex Task Decomposition

| Задача | Thread | Почему | Expected output |
|---|---|---|---|
| 1. Tooling/bootstrap | Отдельный | Задаёт стандарты проекта. | `pyproject`, структура, lint/type/test config. |
| 2. FastAPI/settings/health | Можно тот же после 1 | Небольшое продолжение bootstrap. | App skeleton и `/health`. |
| 3. Pydantic schemas | Отдельный | Контракт должен ревьюиться отдельно. | Schemas + fixture validation tests. |
| 4. Deterministic core | Отдельный | Главная бизнес-логика без side effects. | Pure services + unit tests. |
| 5. DB/Alembic/seed | Отдельный | PostGIS и migrations требуют отдельного внимания. | Models, migrations, active scoring version. |
| 6. Mock providers/cache/dedup | Отдельный | Внешние контракты стабилизируются без API. | Protocols, fake providers, fixtures. |
| 7. API orchestration | Отдельный | Склеивает core + DB + providers. | `/analyze`, `/locations`, integration tests. |
| 8. Report fallback/LLM | Отдельный | AI safety и fallback semantics отдельны. | Fallback-first report service. |
| 9. Optional real providers | Отдельный | Может зависеть от ключей и тарифов. | Real clients behind settings, no CI calls. |
| 10. Streamlit UI | Отдельный | UI строится после стабильного API. | Analyze/result/history/detail pages. |
| 11. Docker/README/polish | Отдельный | Финальная упаковка после известной структуры. | Compose, quickstart, portfolio polish. |
| 12. Final verification | Отдельный review thread | Нужен аудит готовности. | Readiness verdict and fix list. |

## MVP Definition of Done

- Backend стартует локально через `uvicorn app.main:app`.
- `/health` возвращает 200.
- `alembic upgrade head` проходит на чистой PostGIS DB.
- В БД есть active `scoring_versions` для `business_type="pvz"` и `version="v1.0"`.
- Deterministic core покрыт unit tests.
- `POST /api/v1/analyze` работает на mocked providers.
- `GET /api/v1/locations` и `GET /api/v1/locations/{id}` возвращают историю и detail.
- External APIs мокируются в обычных tests/CI.
- Real provider calls доступны только через `pytest -m external`.
- `LLM_ENABLED=false` или пустой LLM key возвращает fallback report.
- Streamlit UI позволяет провести анализ.
- Карта содержит location marker, POI markers и popup с брендом, типом точки, расстоянием.
- Docker Compose поднимает backend, DB и UI.
- README содержит полный quickstart.
- Нет реальных секретов.
- Нет ML, auth, Telegram, H3/heatmap, city-wide search, browser-agent, Avito/Cian parsing.

## Risks And Mitigation

| Риск | Mitigation |
|---|---|
| Внешние API недоступны, платны или rate-limited | Mocked-first pipeline, fixtures in CI, real calls only with `pytest -m external`. |
| Геокодинг возвращает неоднозначный адрес | `ADDRESS_AMBIGUOUS` with suggestions; UI asks user to clarify. |
| Требования маркетплейсов устаревают | MVP returns only `needs_manual_check`; no automatic pass/fail. |
| LLM пишет слишком уверенно | Guardrail prompt, fallback disclaimer, no new facts, report section tests. |
| Scoring выглядит субъективным | Versioned rules, visible score breakdown, manual validation on 30-50 addresses. |
| Финмодель воспринимается как гарантия | Report/UI/README state that income is user hypothesis, not a forecast. |
| PostGIS усложняет local setup | Docker PostGIS for integration; unit tests stay DB-free. |
| MVP слишком большой для одного разработчика | Keep phases independent; real providers and UI only after mocked backend. |
