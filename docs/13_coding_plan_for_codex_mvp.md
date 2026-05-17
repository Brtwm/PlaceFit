# Coding Plan для Codex — MVP PlaceFit

## Общие правила

- Следовать структуре из `docs/03_architecture.md`.
- Использовать стек из `docs/00_overview.md` и `README.md`.
- Не выходить за scope MVP (`docs/02_mvp_scope.md`).
- Принцип «AI объясняет, код считает».
- Все API ключи — в `.env`.
- Не добавлять авторизацию в MVP.
- Не использовать иллюстративные требования маркетплейсов как фактические юридически/операционно точные правила.

---

## Фаза 0: Инициализация проекта

### Задачи
1. Создать `pyproject.toml` с зависимостями.
2. Создать структуру директорий (см. architecture.md).
3. Создать `.env.example`.
4. Создать `Dockerfile` и `docker-compose.yml` (app + postgis).
5. Создать `.gitignore`.

### Файлы
```
pyproject.toml
Dockerfile
docker-compose.yml
.env.example
.gitignore
app/__init__.py
app/main.py              # FastAPI app stub
app/config/settings.py   # Pydantic Settings
```

### Acceptance
- `docker-compose up` запускает app + postgres.
- FastAPI отвечает на `GET /health`.

---

## Фаза 1: Pydantic schemas

### Задачи
1. `AnalysisRequest` — входные данные анализа.
2. `AnalysisResponse` — полный ответ.
3. `ScoreDetails`, `FinanceResult`, `CompetitorInfo`, `ReportResult`.
4. `ErrorResponse` — стандарт ошибок.

### Файлы
```
app/schemas/analysis.py
app/schemas/location.py
app/schemas/competitor.py
app/schemas/score.py
app/schemas/finance.py
app/schemas/report.py
app/schemas/error.py
```

### Acceptance
- Все schemas валидируют JSON из `docs/05_api_contract.md`.

---

## Фаза 2: Core бизнес-логика (без внешних API)

### Задачи
1. `scoring.py` — веса и пороги из `docs/06_scoring_model.md`.
2. `finance.py` — формулы из `docs/07_financial_model.md`.
3. `decision.py` — пороги решений.
4. `confidence.py` — расчёт confidence score.
5. Загрузка активной `scoring_version_id` из БД для сохранения результата анализа.
6. Unit tests для всех модулей.

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

### Acceptance
- `pytest tests/unit/ -v` — все тесты проходят.
- Scoring: любой ввод → score 0–100.
- Finance: дефолтные значения → monthly_costs = 295000.
- Decision: score 82 + profit > 0 → «можно рассматривать».

---

## Фаза 3: Database

### Задачи
1. SQLAlchemy 2.x models для всех MVP таблиц.
2. Alembic init + initial migration.
3. CRUD operations (create, read, list).
4. PostGIS extension setup в migration.

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
```

### Acceptance
- `alembic upgrade head` создаёт все таблицы.
- CRUD: create location → read location → works.
- PostGIS: geom column работает.

---

## Фаза 4: Geocoding + Competitors

### Задачи
1. Provider abstraction (Protocol).
2. 2GIS geocoding provider.
3. 2GIS competitor search provider.
4. Deduplication logic.
5. Distance calculation (PostGIS ST_Distance).
6. Caching layer (DB, TTL).
7. City validation.
8. Error handling + retries (tenacity).
9. Mock tests.

### Файлы
```
app/providers/geocoder/base.py
app/providers/geocoder/dgis.py
app/providers/poi_search/base.py
app/providers/poi_search/dgis.py
app/services/geocoding.py
app/services/competitors.py
app/services/cache.py
tests/unit/test_deduplication.py
tests/unit/test_geocoding_parser.py
tests/fixtures/geocoding/
tests/fixtures/competitors/
```

### Acceptance
- Mock test: 2GIS JSON → parsed competitors.
- Dedup test: дубли удалены.
- Distance: PostGIS ST_Distance returns meters.
- City validation: «Москва» → rejected.

---

## Фаза 5: AI Report

### Задачи
1. LLM provider abstraction.
2. OpenAI provider.
3. Prompt template v1.0 (из `docs/08_ai_report.md`).
4. Fallback template report.
5. Report persistence.
6. Prompt versioning.
7. Если LLM provider failed, но fallback создан, вернуть HTTP 200 и `report.status = "fallback"`.
8. Возвращать `LLM_FAILED` 502 только если отчёт не удалось создать вообще.

### Файлы
```
app/providers/llm/base.py
app/providers/llm/openai.py
app/providers/llm/fallback.py
app/services/report.py
app/config/prompts/v1_0.py
tests/unit/test_report_fallback.py
tests/unit/test_report_schema.py
tests/fixtures/llm/
```

### Acceptance
- Fallback report содержит все числа из analysis JSON.
- OpenAI provider (mock) возвращает текст.
- Report saved to DB with prompt_version.

---

## Фаза 6: API endpoints + Analysis orchestration

### Задачи
1. Analysis service — оркестрация полного pipeline.
2. FastAPI endpoints (все из `docs/05_api_contract.md`).
3. Marketplace requirements check: всегда `needs_manual_check = true`, список ручных проверок и предупреждение о сверке с официальными источниками.
4. Integration tests.

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

### Acceptance
- `POST /api/v1/analyze` с моками → 200, full response.
- LLM error + fallback success → 200, `report.status = "fallback"`.
- LLM error + template report error → 502, `LLM_FAILED`.
- `GET /api/v1/locations` → list.
- `GET /api/v1/locations/1` → detail.
- Error cases: 400, 404, 502.

---

## Фаза 7: Streamlit UI

### Задачи
1. Input form (все поля из MVP scope).
2. Result page (score, map, competitors, finance, report, checklist).
3. History page (table + filters).
4. Map (Folium или Streamlit map).

### Файлы
```
ui/streamlit_app.py
ui/pages/analyze.py
ui/pages/history.py
ui/pages/detail.py
ui/components/map.py
ui/components/score_card.py
```

### Acceptance
- Form → submit → result displayed.
- Map shows competitors.
- History page shows past analyses.

---

## Фаза 8: Polish

### Задачи
1. Docker Compose полный стек (app + db + streamlit).
2. README с quick start.
3. Demo data / seed script.
4. Проверка 30–50 адресов.
5. Screenshots для портфолио.

### Acceptance
- `docker-compose up` → всё работает.
- README: clone → env → up → open browser → analyze.
- 30+ адресов проверены, результаты адекватны.
