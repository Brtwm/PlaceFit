# Coding Plan для Codex — MVP PlaceFit

> Status: historical MVP implementation plan.
>
> MVP / V1.0 is now considered local-demo-ready. This document remains useful
> as build history and implementation context, but it is not the active future
> roadmap. For post-MVP development use [docs/10_roadmap.md](10_roadmap.md).

## Общие правила

- Следовать структуре из `docs/03_architecture.md`.
- Использовать стек из `docs/00_overview.md` и `README.md`.
- Не выходить за scope MVP (`docs/02_mvp_scope.md`).
- Принцип «AI объясняет, код считает».
- Все API ключи — только в `.env`.
- Не добавлять авторизацию, ML, Telegram, H3/heatmap, city-wide search, browser-agent или парсинг Авито/Циан в MVP.
- Не использовать иллюстративные требования маркетплейсов как фактические юридически/операционно точные правила.
- Реальные внешние API не вызываются в обычных tests/CI; real provider checks допускаются только через manual/external marker.

---

## Фаза 0: Repository/bootstrap setup

### Цель
Подготовить Python-проект без бизнес-логики.

### Почему здесь
Все следующие фазы должны запускаться одинаковыми командами и иметь единые правила lint/type/test.

### Задачи
1. Создать `pyproject.toml` с настройками проекта.
2. Создать базовую структуру директорий.
3. Настроить `pytest`, `ruff`, `mypy`.
4. Добавить минимальный import smoke test.

### Файлы
```
pyproject.toml
app/__init__.py
tests/
tests/unit/
tests/integration/
tests/fixtures/
```

### Команды проверки
```bash
pytest
ruff check .
mypy app
```

### Acceptance
- Все команды проходят.
- Нет backend/frontend реализации, DB layer, providers или UI.

### Не входит
FastAPI endpoints, SQLAlchemy, Alembic, Streamlit, Docker, внешние API, LLM.

---

## Фаза 1: FastAPI skeleton, healthcheck, settings

### Цель
Создать минимальный backend process с `/health` и typed settings.

### Почему здесь
Settings и healthcheck нужны до API endpoints и Docker.

### Задачи
1. Создать FastAPI app.
2. Добавить `GET /health`.
3. Добавить Pydantic Settings для `.env`.
4. Зафиксировать LLM defaults:
   - `LLM_ENABLED=false`
   - `LLM_PROVIDER=openai_compatible`
   - `LLM_BASE_URL=`
   - `LLM_API_KEY=`
   - `LLM_MODEL=`

### Файлы
```
app/main.py
app/config/settings.py
app/api/v1/router.py
tests/unit/test_settings.py
tests/integration/test_health.py
```

### Команды проверки
```bash
pytest tests/unit/test_settings.py tests/integration/test_health.py -v
ruff check .
mypy app
```

### Acceptance
- `uvicorn app.main:app` стартует.
- `GET /health` возвращает 200 и `{"status": "ok"}`.
- LLM выключен по умолчанию и не требует API key.

### Не входит
DB sessions, `/analyze`, external clients, Streamlit.

---

## Фаза 2: Pydantic v2 schemas from API contract

### Цель
Зафиксировать API request/response contract до реализации сервисов.

### Почему здесь
Схемы становятся границей между API, services, UI и тестами.

### Задачи
1. `AnalysisRequest` — входные данные анализа.
2. `AnalysisResponse` — полный ответ из `docs/05_api_contract.md`.
3. `ScoreDetails`, `FinanceResult`, `CompetitorInfo`, `ReportResult`.
4. `ErrorResponse` — стандарт ошибок.
5. Валидировать, что `business_type` в MVP только `pvz`.

### Файлы
```
app/schemas/analysis.py
app/schemas/location.py
app/schemas/competitor.py
app/schemas/score.py
app/schemas/finance.py
app/schemas/report.py
app/schemas/error.py
tests/unit/test_schemas.py
tests/fixtures/api/
```

### Команды проверки
```bash
pytest tests/unit/test_schemas.py -v
ruff check app tests
mypy app
```

### Acceptance
- Schemas валидируют JSON examples из `docs/05_api_contract.md`.
- `marketplace_requirements` содержит только `ozon`, `wildberries`, `yandex_market`.
- `ReportResult.provider` допускает `openai_compatible` и `fallback`.

### Не входит
Расчёты, БД, HTTP endpoints, providers.

---

## Фаза 3: Deterministic core без DB

### Цель
Реализовать rule-based scoring, finance, confidence и decision как чистые deterministic modules.

### Почему здесь
Главный принцип MVP — «код считает». Эти модули должны тестироваться без БД, API и LLM.

### Задачи
1. `scoring.py` — веса и пороги из `docs/06_scoring_model.md`.
2. `finance.py` — формулы из `docs/07_financial_model.md`.
3. `decision.py` — пороги решений.
4. `confidence.py` — расчёт confidence score.
5. Unit tests для всех модулей.

### Файлы
```
app/services/scoring.py
app/services/finance.py
app/services/decision.py
app/services/confidence.py
app/config/scoring_rules.py
tests/unit/test_scoring.py
tests/unit/test_finance.py
tests/unit/test_decision.py
tests/unit/test_confidence.py
```

### Команды проверки
```bash
pytest tests/unit/test_scoring.py tests/unit/test_finance.py tests/unit/test_decision.py tests/unit/test_confidence.py -v
ruff check app tests
mypy app
```

### Acceptance
- Любой валидный ввод даёт `total_score` в диапазоне 0–100.
- Одинаковый ввод даёт одинаковый результат.
- Default finance даёт `monthly_costs = 295000`.
- `score=82` и `net_profit > 0` дают решение `можно рассматривать`.
- В deterministic core нет импортов SQLAlchemy, providers или LLM.

### Не входит
`scoring_version_id`, DB persistence, API orchestration.

---

## Фаза 4: Database layer, Alembic, scoring seed

### Цель
Создать persistence layer и обязательную активную версию скоринга `pvz/v1.0`.

### Почему здесь
После чистого core можно сохранять результаты анализа и привязку к `scoring_version_id`.

### Задачи
1. SQLAlchemy 2.x models для MVP таблиц из `docs/04_data_model.md`.
2. Alembic init + initial migration.
3. PostGIS extension setup в migration.
4. Seed/default active scoring version `business_type=pvz`, `version=v1.0`.
5. Минимальные CRUD/read helpers для history/detail.

### Файлы
```
app/models/location.py
app/models/poi.py
app/models/score.py
app/models/finance.py
app/models/report.py
app/models/scoring_version.py
app/models/marketplace_requirement.py
app/db/session.py
app/db/base.py
alembic/
alembic.ini
alembic/versions/001_initial.py
tests/integration/test_db_migrations.py
```

### Команды проверки
```bash
alembic upgrade head
pytest tests/integration/test_db_migrations.py -v
```

### Acceptance
- Fresh PostGIS DB migrates from zero.
- `scoring_versions` содержит одну active версию для `pvz/v1.0`.
- `scores.scoring_version_id` ссылается на `scoring_versions`.
- `trend_score` не добавляется в MVP `scores`.

### Не входит
External providers, LLM, Streamlit.

---

## Фаза 5: Mocked providers, fixtures, cache, dedup

### Цель
Стабилизировать внешние контракты без реальных API.

### Почему здесь
API orchestration должна сначала работать на deterministic fixtures.

### Задачи
1. Provider Protocols для geocoding и POI search.
2. Mocked 2GIS geocoding/POI provider.
3. Mocked Yandex geocoding fallback.
4. OSM POI fallback fixtures.
5. Deduplication logic.
6. City validation для Краснодара.
7. DB cache TTL contract.

### Файлы
```
app/providers/geocoder/base.py
app/providers/geocoder/fake.py
app/providers/poi_search/base.py
app/providers/poi_search/fake.py
app/services/geocoding.py
app/services/competitors.py
app/services/cache.py
tests/unit/test_deduplication.py
tests/unit/test_geocoding_parser.py
tests/fixtures/geocoding/
tests/fixtures/competitors/
```

### Команды проверки
```bash
pytest tests/unit/test_deduplication.py tests/unit/test_geocoding_parser.py -v
pytest -v --tb=short
```

### Acceptance
- Tests не делают network calls.
- Ambiguous address возвращает suggestions.
- Москва отклоняется как `CITY_NOT_SUPPORTED`.
- Дубли удаляются по `(source, external_id)` и close-distance same-brand logic.
- Yandex fallback есть как mocked provider; real Yandex не блокирует MVP.

### Не входит
Реальные 2GIS/Yandex/OSM clients, `/analyze`, LLM.

---

## Фаза 6: API endpoints and analysis orchestration

### Цель
Собрать полный backend pipeline на mocked providers.

### Почему здесь
К этому моменту есть schemas, deterministic core, DB и mocked providers.

### Задачи
1. Analysis service — orchestration полного pipeline.
2. FastAPI endpoints из `docs/05_api_contract.md`.
3. Marketplace check: только `ozon`, `wildberries`, `yandex_market`, всегда `needs_manual_check=true`.
4. History/detail endpoints.
5. Error mapping в стандартный `ErrorResponse`.

### Файлы
```
app/services/analysis.py
app/services/marketplace.py
app/api/v1/router.py
app/api/v1/endpoints/analyze.py
app/api/v1/endpoints/locations.py
app/api/v1/endpoints/geocode.py
app/api/v1/endpoints/competitors.py
app/api/v1/endpoints/report.py
app/api/v1/deps.py
tests/integration/test_analyze.py
tests/integration/test_locations.py
```

### Команды проверки
```bash
pytest tests/integration/test_analyze.py tests/integration/test_locations.py -v
pytest -v --tb=short
```

### Acceptance
- `POST /api/v1/analyze` с mocked providers возвращает 200 и full response.
- Анализ сохраняется в DB.
- `GET /api/v1/locations` возвращает список.
- `GET /api/v1/locations/{id}` возвращает detail.
- Error cases покрыты: 400, 404, 422, 502.
- Marketplace response не содержит других marketplace requirements кроме Ozon/WB/Yandex Market.

### Не входит
Real provider network calls, Streamlit, production deployment.

---

## Фаза 7: Fallback-first AI report

### Цель
Гарантировать отчёт без LLM и подключить OpenAI-compatible LLM как optional provider.

### Почему здесь
LLM должен получать только готовый analysis JSON после deterministic расчётов.

### Задачи
1. LLM provider abstraction.
2. OpenAI-compatible provider.
3. Prompt template v1.0 из `docs/08_ai_report.md`.
4. Fallback template report.
5. Report persistence.
6. Prompt versioning.
7. `LLM_ENABLED=false` или пустой key -> fallback report.

### Файлы
```
app/providers/llm/base.py
app/providers/llm/openai_compatible.py
app/providers/llm/fallback.py
app/services/report.py
app/config/prompts/v1_0.py
tests/unit/test_report_fallback.py
tests/unit/test_report_schema.py
tests/fixtures/llm/
```

### Команды проверки
```bash
pytest tests/unit/test_report_fallback.py tests/unit/test_report_schema.py -v
pytest tests/integration/test_analyze.py -v
```

### Acceptance
- Fallback report работает без LLM API key.
- OpenAI-compatible mock success возвращает текст.
- LLM error + fallback success -> HTTP 200, `report.status = "fallback"`.
- LLM error + fallback error -> HTTP 502, `LLM_FAILED`.
- LLM не имеет доступа к DB, shell, внешним API или секретам.

### Не входит
Hardcoded LLM vendor/model, real LLM calls in CI.

---

## Фаза 8: Optional real providers behind settings

### Цель
Подключить реальные provider clients как optional runtime layer.

### Почему здесь
Real API не должны блокировать mocked MVP pipeline.

### Задачи
1. Реальный 2GIS provider behind settings.
2. Optional OSM fallback provider.
3. Provider factory по settings.
4. Timeout/retry policy.
5. Manual/external tests marker.

### Файлы
```
app/providers/geocoder/dgis.py
app/providers/poi_search/dgis.py
app/providers/poi_search/osm.py
app/providers/factory.py
tests/unit/test_provider_factories.py
tests/external/
```

### Команды проверки
```bash
pytest tests/unit/test_provider_factories.py -v
pytest -v --tb=short
pytest -m external
```

### Acceptance
- Без API keys приложение работает на mocked/fallback path.
- Обычный `pytest` не вызывает реальные внешние API.
- Real 2GIS provider optional.
- Real Yandex provider не блокирует MVP readiness.

### Не входит
Avito/Cian parsing, browser-agent, scraping.

---

## Фаза 9: Streamlit UI with streamlit-folium

### Цель
Дать пользователю полный MVP flow в Streamlit.

### Почему здесь
UI должен строиться поверх стабильного backend API.

### Задачи
1. Input form со всеми MVP полями.
2. Result page: score, decision, finance, report, checklist.
3. History page.
4. Detail page.
5. Map через `streamlit-folium` + `folium`.

### Файлы
```
ui/streamlit_app.py
ui/pages/analyze.py
ui/pages/history.py
ui/pages/detail.py
ui/components/map.py
ui/components/score_card.py
```

### Зависимости этой фазы
```
streamlit
folium
streamlit-folium
```

### Команды проверки
```bash
streamlit run ui/streamlit_app.py
pytest -v --tb=short
```

### Acceptance
- Form submit вызывает backend `/api/v1/analyze`.
- Result page показывает score, confidence, decision, finance, report, checklist.
- Map показывает маркер анализируемой локации.
- Map показывает маркеры конкурентов/POI.
- Popup содержит бренд, тип точки и расстояние.
- History page показывает сохранённые анализы.

### Не входит
Heatmap, H3, city-wide search, routing, сложные геослои, auth.

---

## Фаза 10: Docker Compose, README quickstart, portfolio polish

### Цель
Сделать MVP запускаемым и презентабельным.

### Почему здесь
Compose и README должны отражать уже реализованную структуру.

### Задачи
1. Dockerfile для backend.
2. Docker Compose: backend + postgis + streamlit.
3. Alembic migration on startup или документированная команда.
4. README quickstart.
5. Demo seed/screenshot checklist.

### Файлы
```
Dockerfile
docker-compose.yml
README.md
```

### Команды проверки
```bash
docker compose up --build
docker compose exec backend pytest -v --tb=short
```

### Acceptance
- Fresh clone path задокументирован.
- Backend, DB и Streamlit стартуют.
- README не требует реальных secrets для fallback/demo path.
- `.env.example` не содержит реальных secrets.

### Не входит
Production deployment, CI/CD, managed DB, monitoring.

---

## Фаза 11: Final verification checklist

### Цель
Проверить готовность MVP без добавления новых фич.

### Проверки
```bash
pytest -v --tb=short
ruff check .
mypy app
alembic upgrade head
docker compose up --build
```

### Acceptance
- Backend стартует.
- DB миграции проходят.
- Deterministic core покрыт tests.
- API endpoints работают на mocked providers.
- External APIs можно мокать.
- Fallback report работает без LLM key.
- Streamlit UI позволяет провести анализ.
- История анализов доступна.
- Docker Compose поднимает проект.
- README содержит полный quickstart.
- Нет реальных секретов.
- GitHub presentation выглядит презентабельно.

---

## Рекомендуемая декомпозиция Codex-задач

| Задача | Thread | Expected output |
|---|---|---|
| 1. Tooling/bootstrap | Отдельный | `pyproject`, структура, lint/type/test config |
| 2. FastAPI/settings/health | Можно тот же после 1 | App skeleton и `/health` |
| 3. Pydantic schemas | Отдельный | Schemas + fixture validation tests |
| 4. Deterministic core | Отдельный | Pure services + unit tests |
| 5. DB/Alembic/seed | Отдельный | Models, migrations, active scoring version |
| 6. Mock providers/cache/dedup | Отдельный | Protocols, fake providers, fixtures |
| 7. API orchestration | Отдельный | `/analyze`, `/locations`, integration tests |
| 8. Report fallback/LLM | Отдельный | Fallback-first report service |
| 9. Optional real providers | Отдельный | Real clients behind settings, no CI calls |
| 10. Streamlit UI | Отдельный | Analyze/result/history/detail pages |
| 11. Docker/README/polish | Отдельный | Compose, quickstart, portfolio polish |
| 12. Final verification | Отдельный review thread | Readiness verdict and fix list |
