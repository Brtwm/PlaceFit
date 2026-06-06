# API Contract — PlaceFit MVP

## Base URL

```
http://localhost:8000/api/v1
```

## Error format (все endpoints)

```json
{
  "error": {
    "code": "GEOCODING_FAILED",
    "message": "Не удалось геокодировать адрес",
    "details": "2GIS API timeout after 10s"
  }
}
```

Коды ошибок:
- `VALIDATION_ERROR` (422) — невалидные входные данные
- `GEOCODING_FAILED` (502) — ошибка геокодинга
- `CITY_NOT_SUPPORTED` (400) — адрес вне Краснодара
- `ADDRESS_AMBIGUOUS` (400) — несколько вариантов адреса
- `COMPETITOR_SEARCH_FAILED` (502) — ошибка поиска конкурентов
- `LLM_FAILED` (502) — отчёт не удалось создать вообще
- `NOT_FOUND` (404) — анализ не найден
- `INTERNAL_ERROR` (500) — внутренняя ошибка

Если `LLM_ENABLED=false`, LLM API key не задан или LLM provider недоступен, но fallback report успешно создан, endpoint возвращает HTTP 200 с `report.status = "fallback"`.

---

## POST /api/v1/analyze

Полный анализ адреса.

### Request

```json
{
  "address": "Краснодар, ул. Восточно-Кругликовская, 30",
  "business_type": "pvz",
  "rent": 85000,
  "area_m2": 35,
  "floor": 1,
  "first_floor": true,
  "separate_entrance": true,
  "parking": true,
  "signage_possible": true,
  "storage_area": true,
  "repair_condition": "normal",
  "new_residential_area": true,
  "high_density_area": true,
  "bus_stop_nearby": true,
  "good_visibility": true,
  "expected_gross_income_by_user": 360000,
  "investment": 600000,
  "desired_profit": 80000
}
```

### Response (200)

```json
{
  "location": {
    "id": 1,
    "address": "Краснодар, ул. Восточно-Кругликовская, 30",
    "normalized_address": "г Краснодар, ул Восточно-Кругликовская, д 30",
    "lat": 45.035,
    "lon": 39.028
  },
  "competitors": {
    "competitors_300m": 1,
    "competitors_500m": 3,
    "competitors_700m": 5,
    "nearest_competitor_distance_m": 180,
    "average_competitor_distance_m": 420,
    "list": [
      {
        "name": "Ozon",
        "brand": "ozon",
        "category": "pvz",
        "address": "ул. Восточно-Кругликовская, 28",
        "lat": 45.036,
        "lon": 39.029,
        "distance_m": 180,
        "rating": 4.2,
        "reviews_count": 156,
        "source": "2gis"
      }
    ]
  },
  "score": {
    "total_score": 82,
    "confidence_score": 90,
    "scoring_version": "v1.0",
    "decision": "можно рассматривать",
    "details": {
      "demand_score": 35,
      "competition_score": 12,
      "rent_score": 15,
      "premises_score": 10,
      "accessibility_score": 10
    }
  },
  "finance": {
    "monthly_costs": 295000,
    "required_gross_income": 375000,
    "expected_gross_income_by_user": 360000,
    "net_profit": 65000,
    "payback_months": 9.2
  },
  "marketplace_requirements": {
    "ozon": {
      "status": "needs_manual_check",
      "needs_manual_check": true,
      "manual_checks": ["Проверить зону открытия на официальном сайте Ozon"],
      "warning": "Требования маркетплейсов нужно сверить с официальными источниками."
    },
    "wildberries": {
      "status": "needs_manual_check",
      "needs_manual_check": true,
      "manual_checks": ["Сверить актуальные требования к площади, складу, этажу и входу"],
      "warning": "Требования маркетплейсов нужно сверить с официальными источниками."
    },
    "yandex_market": {
      "status": "needs_manual_check",
      "needs_manual_check": true,
      "manual_checks": ["Уточнить формат ПВЗ и зону открытия"],
      "warning": "Требования маркетплейсов нужно сверить с официальными источниками."
    }
  },
  "report": {
    "status": "success",
    "text": "## Краткий вывод\n\nАдрес ...",
    "provider": "openai_compatible",
    "model": "runtime-configured",
    "prompt_version": "v1.0"
  },
  "checklist": [
    "Проверить проходимость утром, днём и вечером",
    "Проверить договор аренды и арендные каникулы",
    "Проверить конкурентов вручную в 2ГИС"
  ],
  "data_sources": [
    {"source": "2gis", "data_type": "geocoding", "fetched_at": "2026-05-14T10:00:00Z", "confidence": 0.95},
    {"source": "2gis", "data_type": "competitors", "fetched_at": "2026-05-14T10:00:00Z"},
    {"source": "yandex", "data_type": "competitors", "fetched_at": "2026-05-14T10:00:00Z"}
  ],
  "created_at": "2026-05-14T10:00:05Z"
}
```

### Response при ambiguous address (400)

```json
{
  "error": {
    "code": "ADDRESS_AMBIGUOUS",
    "message": "Найдено несколько вариантов адреса",
    "suggestions": [
      {"address": "г Краснодар, ул Восточно-Кругликовская, д 30", "lat": 45.035, "lon": 39.028},
      {"address": "г Краснодар, ул Восточно-Кругликовская, д 30/1", "lat": 45.036, "lon": 39.029}
    ]
  }
}
```

---

## POST /api/v1/locations/compare — V1.2 contract

Status: **implemented in V1.2-3 as a backend API endpoint**.

`POST /api/v1/analyze` remains unchanged. Compare mode reuses the existing
single-address `AnalysisRequest` shape for newly entered candidates. Saved
analysis references as compare inputs remain deferred. V1.2-4 adds DB-backed
compare session persistence: successful API compare runs return a populated
`compare_id` and store full request/response snapshots. The schema keeps
`compare_id` nullable for backward compatibility and service-level use without a
DB session.

LLM output is not used for score, confidence, finance, decision, ranking, or
candidate ordering. Ranking metadata must be deterministic and derived from
visible response fields only.

### Request

`candidates` must contain 2–5 items. Each `analysis_request` has the exact same
field shape as `POST /api/v1/analyze`.

```json
{
  "candidates": [
    {
      "label": "Вариант A",
      "analysis_request": {
        "address": "Краснодар, ул. Восточно-Кругликовская, 30",
        "business_type": "pvz",
        "rent": 85000,
        "area_m2": 35,
        "floor": 1,
        "first_floor": true,
        "separate_entrance": true,
        "parking": true,
        "signage_possible": true,
        "storage_area": true,
        "repair_condition": "normal",
        "new_residential_area": true,
        "high_density_area": true,
        "bus_stop_nearby": true,
        "good_visibility": true,
        "expected_gross_income_by_user": 360000,
        "investment": 600000,
        "desired_profit": 80000
      }
    },
    {
      "label": "Вариант B",
      "analysis_request": {
        "address": "Краснодар, ул. Красная, 1",
        "business_type": "pvz",
        "rent": 95000,
        "area_m2": 40,
        "floor": 1,
        "first_floor": true,
        "separate_entrance": true,
        "parking": false,
        "signage_possible": true,
        "storage_area": true,
        "repair_condition": "normal",
        "new_residential_area": false,
        "high_density_area": true,
        "bus_stop_nearby": true,
        "good_visibility": true,
        "expected_gross_income_by_user": 340000,
        "investment": 600000,
        "desired_profit": 80000
      }
    }
  ]
}
```

`label` is optional. If provided, it must be non-empty.

### Response (200)

Compare responses can contain successful candidates, failed candidates, or both.
When the API saves the compare session successfully, `compare_id` contains the
saved `compare_sessions.id`.

```json
{
  "compare_id": 1,
  "created_at": "2026-05-31T12:00:00Z",
  "ranking_rules": {
    "version": "v1.2-2",
    "description": "Successful candidates are ranked deterministically from visible analysis fields. LLM output is not used for ranking.",
    "sort_keys": [
      {
        "field": "score.total_score",
        "direction": "desc",
        "nulls": "none",
        "description": "Higher deterministic total score ranks first."
      },
      {
        "field": "score.confidence_score",
        "direction": "desc",
        "nulls": "none",
        "description": "Higher deterministic confidence breaks score ties."
      },
      {
        "field": "score.decision",
        "direction": "asc",
        "nulls": "none",
        "description": "Decision severity order breaks remaining ties."
      },
      {
        "field": "finance.net_profit",
        "direction": "desc",
        "nulls": "last",
        "description": "Higher known net profit breaks remaining ties."
      },
      {
        "field": "finance.payback_months",
        "direction": "asc",
        "nulls": "last",
        "description": "Shorter payback breaks ties when available."
      },
      {
        "field": "input_index",
        "direction": "asc",
        "nulls": "none",
        "description": "Original input order is the final stable tie-break."
      }
    ],
    "decision_severity_order": [
      "можно рассматривать",
      "проверить дополнительно",
      "скорее не открывать"
    ],
    "uses_llm": false
  },
  "ranked_candidates": [
    {
      "candidate_id": "candidate-1",
      "input_index": 0,
      "rank": 1,
      "label": "Вариант A",
      "input_address": "Краснодар, ул. Восточно-Кругликовская, 30",
      "status": "success",
      "source_analysis_id": null,
      "location_summary": {
        "id": 1,
        "address": "Краснодар, ул. Восточно-Кругликовская, 30",
        "normalized_address": "г Краснодар, ул Восточно-Кругликовская, д 30",
        "lat": 45.035,
        "lon": 39.028
      },
      "score": {
        "total_score": 82,
        "confidence_score": 90,
        "scoring_version": "v1.0",
        "decision": "можно рассматривать",
        "details": {
          "demand_score": 35,
          "competition_score": 12,
          "rent_score": 15,
          "premises_score": 10,
          "accessibility_score": 10
        }
      },
      "finance": {
        "monthly_costs": 295000,
        "required_gross_income": 375000,
        "expected_gross_income_by_user": 360000,
        "net_profit": 65000,
        "payback_months": 9.2
      },
      "competitors": {
        "competitors_300m": 1,
        "competitors_500m": 3,
        "competitors_700m": 5,
        "nearest_competitor_distance_m": 180,
        "average_competitor_distance_m": 420
      },
      "assumptions": ["expected_gross_income_by_user is a user hypothesis"],
      "warnings": ["Marketplace requirements need manual verification"],
      "trade_offs": ["Higher score but longer payback than another candidate"]
    }
  ],
  "failed_candidates": [
    {
      "candidate_id": "candidate-2",
      "input_index": 1,
      "label": "Вариант B",
      "input_address": "Краснодар, Восточно-Кругликовская 30",
      "status": "failed",
      "error": {
        "code": "ADDRESS_AMBIGUOUS",
        "message": "Найдено несколько вариантов адреса",
        "suggestions": [
          {
            "address": "г Краснодар, ул Восточно-Кругликовская, д 30",
            "lat": 45.035,
            "lon": 39.028,
            "confidence": 0.82
          }
        ]
      }
    }
  ],
  "summary": {
    "requested_count": 2,
    "successful_count": 1,
    "failed_count": 1
  }
}
```

### Ranking rules

The initial deterministic ranking rule is:

1. Sort successful candidates by `score.total_score` descending.
2. Tie-break by `score.confidence_score` descending.
3. Tie-break by `score.decision` severity, best to worst:
   `можно рассматривать`, `проверить дополнительно`, `скорее не открывать`.
4. Tie-break by `finance.net_profit` descending, with missing values last.
5. Tie-break by `finance.payback_months` ascending, with missing values last.
6. Final tie-break by original `input_index` ascending.

`ranking_rules.uses_llm` must always be `false`. If `trade_offs` text is
included, it must be derived only from fields visible in the compare response.
Stored compare snapshots preserve this historical ranking context and must not
be rebuilt from current provider, scoring, finance, report, or ranking logic.

### Error policy

- Invalid request shape, including fewer than 2 or more than 5 candidates,
  unsupported saved-analysis reference shapes, and unsupported nested
  `business_type` values, returns HTTP 422.
- Candidate analysis failures should be represented in `failed_candidates` when
  compare can continue for other candidates.
- Partial failures return HTTP 200 with successful candidates in
  `ranked_candidates` and candidate-level errors in `failed_candidates`.
- If all candidate analyses fail but compare can represent those failures, the
  endpoint returns HTTP 200 with an empty `ranked_candidates` list and populated
  `failed_candidates`.
- Request-level errors should be used only when compare cannot run at all.
- Ambiguous geocoding should expose candidate-level `error.suggestions` using
  the existing geocoding suggestion shape.

---

## GET /api/v1/locations/compare/{compare_id} — V1.2 saved session

Returns the saved public compare response snapshot for a previously persisted
compare run. Loading a saved compare session does not rerun geocoding, POI
search, scoring, finance, report generation, or ranking.

### Response (200)

The response shape is the same as `POST /api/v1/locations/compare` and is loaded
from `compare_sessions.response_snapshot`.

### Response when not found (404)

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Сессия сравнения не найдена"
  }
}
```

---

## GET /api/v1/locations

Список проверенных адресов.

### Query params

| Param | Type | Description |
|-------|------|-------------|
| business_type | string | Фильтр по типу (default: pvz) |
| min_score | int | Минимальный score |
| max_score | int | Максимальный score |
| decision | string | Фильтр по решению |
| date_from | date | Дата от |
| date_to | date | Дата до |
| limit | int | Лимит (default: 50) |
| offset | int | Offset |

### Response (200)

```json
{
  "items": [
    {
      "id": 1,
      "address": "ул. Восточно-Кругликовская, 30",
      "business_type": "pvz",
      "rent": 85000,
      "total_score": 82,
      "confidence_score": 90,
      "decision": "можно рассматривать",
      "net_profit": 65000,
      "payback_months": 9.2,
      "created_at": "2026-05-14T10:00:05Z"
    }
  ],
  "total": 1
}
```

---

## GET /api/v1/locations/{id}

Детальная карточка анализа. Возвращает полную структуру как POST /analyze response.

---

## POST /api/v1/geocode

### Request
```json
{"address": "Краснодар, ул. Красная, 1"}
```

### Response (200)
```json
{
  "results": [
    {"address": "г Краснодар, ул Красная, д 1", "lat": 45.025, "lon": 38.971, "confidence": 0.95}
  ],
  "source": "2gis"
}
```

---

## POST /api/v1/competitors/search

### Request
```json
{"lat": 45.035, "lon": 39.028, "radius_m": 700, "business_type": "pvz"}
```

### Response (200)
```json
{
  "competitors": [...],
  "counts": {"300m": 1, "500m": 3, "700m": 5},
  "source": "2gis",
  "fetched_at": "2026-05-14T10:00:00Z"
}
```

---

## POST /api/v1/report/generate

Status: **not implemented in MVP / V1.0**. Report generation currently happens
inside `POST /api/v1/analyze`. A separate regeneration endpoint may be added in
a future reporting iteration if there is a product need.

Генерация AI-отчёта по готовому JSON (для перегенерации).

### Request
```json
{"location_id": 1}
```

### Response (200)
```json
{
  "status": "success",
  "text": "...",
  "provider": "openai_compatible",
  "model": "runtime-configured",
  "prompt_version": "v1.0"
}
```

---

## Future endpoints (not MVP / V1.0)

| Endpoint | Версия | Назначение |
|----------|--------|-----------|
| POST /api/v1/exports | V1.3 | Markdown/PDF/Excel export |
| POST /api/v1/locations/{id}/reanalyze | V1.4 | Manual refresh saved location |
| GET /api/v1/locations/{id}/deltas | V1.4 | Delta between saved analyses |
| GET /api/v1/scoring-versions/compare | V1.5 | Scoring rule version comparison |
| GET /api/v1/zones/heatmap | V2 | PVZ-only city-wide H3/grid data |

Autonomous trendwatcher endpoints are deferred/conditional and should not be
added until legal, stable, useful data sources are proven.
