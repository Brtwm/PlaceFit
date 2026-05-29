# Архитектура — PlaceFit MVP

## Верхний уровень

```
User → Streamlit UI → FastAPI Backend → Services → PostgreSQL/PostGIS
                                            ↓
                               Provider abstractions (fake / 2GIS / OSM)
                                            ↓
                        Report provider (fallback / OpenAI-compatible LLM)
```

## Структура проекта

```
PlaceFit/
├── app/
│   ├── api/v1/
│   │   ├── router.py
│   │   ├── endpoints/
│   │   │   ├── analyze.py      # POST /api/v1/analyze
│   │   │   ├── locations.py    # GET /api/v1/locations, GET /api/v1/locations/{id}
│   │   │   ├── geocode.py      # POST /api/v1/geocode
│   │   │   ├── competitors.py  # POST /api/v1/competitors/search
│   │   │   └── report.py       # future report regeneration endpoint, not MVP
│   │   └── deps.py
│   ├── services/
│   │   ├── geocoding.py        # Геокодинг + кэш
│   │   ├── competitors.py      # Поиск + дедупликация
│   │   ├── scoring.py          # Rule-based scoring
│   │   ├── confidence.py       # Confidence score
│   │   ├── finance.py          # Финансовая модель
│   │   ├── marketplace.py      # Требования маркетплейсов
│   │   ├── decision.py         # Решение по порогам
│   │   ├── report.py           # AI-отчёт + fallback
│   │   ├── analysis.py         # Оркестрация полного анализа
│   │   └── cache.py            # Кэширование
│   ├── providers/
│   │   ├── geocoder/
│   │   │   ├── base.py         # Protocol
│   │   │   ├── dgis.py         # 2GIS
│   │   │   └── fake.py         # deterministic demo/fallback fixtures
│   │   ├── poi_search/
│   │   │   ├── base.py
│   │   │   ├── dgis.py
│   │   │   └── osm.py
│   │   └── llm/
│   │       ├── base.py
│   │       ├── openai_compatible.py
│   │       └── fallback.py
│   ├── models/                 # SQLAlchemy ORM
│   │   ├── location.py
│   │   ├── poi.py
│   │   ├── score.py
│   │   ├── finance.py
│   │   ├── report.py
│   │   └── scoring_version.py
│   ├── schemas/                # Pydantic v2
│   │   ├── analysis.py
│   │   ├── location.py
│   │   ├── competitor.py
│   │   ├── score.py
│   │   ├── finance.py
│   │   └── report.py
│   ├── config/
│   │   ├── settings.py         # Pydantic Settings
│   │   └── scoring_rules.py    # Веса и пороги
│   ├── db/
│   │   ├── session.py
│   │   └── base.py
│   └── main.py                 # FastAPI app
├── alembic/
├── ui/
│   └── streamlit_app.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── .env.example
```

## Data flow: полный анализ адреса

```
1. Input validation (Pydantic AnalysisRequest)
     ↓
2. Geocoding
   ├── Check cache (DB)
   ├── Use fake demo provider by default or optional 2GIS provider
   ├── Normalize address
   └── Validate city = Краснодар
     ↓
3. Competitor search
   ├── Check cache (DB, TTL 7-14 дней)
   ├── Use fake demo provider by default or optional 2GIS/OSM provider
   ├── Deduplicate (by external_id + distance threshold)
   └── Save POIs to DB
     ↓
4. Distance calculation (PostGIS ST_Distance)
   ├── competitors_300m, competitors_500m, competitors_700m
   ├── nearest_competitor_distance_m
   └── average_competitor_distance_m
     ↓
5. Scoring (deterministic, rule-based)
   ├── demand_score (max 35)
   ├── competition_score (max 25)
   ├── rent_score (max 20)
   ├── premises_score (max 10)
   └── accessibility_score (max 10)
     ↓
6. Confidence score (0-100)
     ↓
7. Finance calculation
   ├── monthly_costs
   ├── required_gross_income
   ├── net_profit (if expected_income provided)
   └── payback_months (if net_profit > 0)
     ↓
8. Marketplace requirements check
     ↓
9. Decision (score + finance thresholds)
     ↓
10. Build analysis JSON
     ↓
11. Report generation (OpenAI-compatible LLM when enabled → fallback template)
     ↓
12. Save all to DB
     ↓
13. Return AnalysisResponse
```

## Паттерны

### Provider abstraction
Каждый внешний сервис за Protocol-интерфейсом. Позволяет подменять, мокать, добавлять fallback.

### Scoring versioning
В MVP правила хранятся в таблице `scoring_versions`, а каждый анализ привязан к `scoring_version_id`. Управление версиями, сравнение результатов между версиями и история изменений относятся к V1.5 scoring governance после V1.1 validation, V1.2 compare mode, V1.3 export polish и V1.4 saved-location refresh.

### Кэш в БД
Геокодинг TTL 30 дней, POI TTL 7–14 дней. PostgreSQL, не Redis (упрощение для MVP).

### Fallback chains
```
Geocoding: fake by default; optional 2GIS when configured; clear error on failure
POI: fake by default; optional 2GIS or OSM when configured
LLM: OpenAI-compatible provider when enabled → template fallback
```

## Extension points (post-MVP)

| Точка | Версия | Как расширять |
|-------|--------|--------------|
| Manual validation | V1.1 | Validation cases and known limitations |
| Compare mode | V1.2 | Compare API/UI over deterministic per-address analyses |
| Export/reporting | V1.3 | Markdown/PDF/Excel from existing analysis JSON |
| Saved location refresh | V1.4 | Re-run analysis and show deltas |
| Scoring governance | V1.5 | Version comparison and auditable rule changes |
| Marketplace maturity | V1.5 | Source-tracked manual-check rules |
| H3/Heatmap | V2 | PVZ-only city-wide module after validation |
| New businesses | V3 | Separate scoring profiles after PVZ validation |
| ML forecast | V3 | Dataset/backtesting-driven layer, not a rule-based replacement |
