# Архитектура — PlaceFit MVP

## Верхний уровень

```
User → Streamlit UI → FastAPI Backend → Services → PostgreSQL/PostGIS
                                            ↓
                                      External APIs (2GIS, Yandex, OSM)
                                            ↓
                                      LLM Provider (OpenAI)
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
│   │   │   └── report.py       # POST /api/v1/report/generate
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
│   │   │   └── yandex.py       # Yandex
│   │   ├── poi_search/
│   │   │   ├── base.py
│   │   │   ├── dgis.py
│   │   │   └── osm.py
│   │   └── llm/
│   │       ├── base.py
│   │       ├── openai.py
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
   ├── Call 2GIS API (or Yandex fallback)
   ├── Normalize address
   └── Validate city = Краснодар
     ↓
3. Competitor search
   ├── Check cache (DB, TTL 7-14 дней)
   ├── Call 2GIS API (categories: Ozon, WB, Yandex Market, СДЭК, Boxberry, Почта, постаматы)
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
11. AI report (OpenAI → fallback template)
     ↓
12. Save all to DB
     ↓
13. Return AnalysisResponse
```

## Паттерны

### Provider abstraction
Каждый внешний сервис за Protocol-интерфейсом. Позволяет подменять, мокать, добавлять fallback.

### Scoring versioning
В MVP правила хранятся в таблице `scoring_versions`, а каждый анализ привязан к `scoring_version_id`. UI/admin для управления версиями, сравнение результатов между версиями и история изменений относятся к V1.5.

### Кэш в БД
Геокодинг TTL 30 дней, POI TTL 7–14 дней. PostgreSQL, не Redis (упрощение для MVP).

### Fallback chains
```
Geocoding: 2GIS → Yandex → error с сообщением
POI: 2GIS → OSM → error с сообщением
LLM: OpenAI → template fallback
```

## Extension points (будущее)

| Точка | Версия | Как расширять |
|-------|--------|--------------|
| Новые бизнесы | V3 | Новые scoring rules + business_type |
| Compare mode | V1.5 | Новый endpoint + UI page |
| H3/Heatmap | V2 | Новый модуль + batch scoring |
| Trendwatcher | V2 | Новый сервис + таблица signals |
| ML forecast | V3 | Новый provider, не заменяет rule-based |
