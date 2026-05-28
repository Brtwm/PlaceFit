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

## Будущие endpoints (НЕ MVP)

| Endpoint | Версия | Назначение |
|----------|--------|-----------|
| POST /api/v1/locations/compare | V1.5 | Сравнение 2–5 адресов |
| GET /api/v1/monitoring/alerts | V1.5 | Алерты мониторинга |
| GET /api/v1/zones/heatmap | V2 | H3 heatmap данные |
| GET /api/v1/trends | V2 | Сигналы trendwatcher |
