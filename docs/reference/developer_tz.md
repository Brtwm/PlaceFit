# AI Location Agent — обновлённое ТЗ для разработчика

> Status: historical / superseded reference.
>
> MVP / V1.0 is now considered local-demo-ready under the PlaceFit name. This
> document remains useful as background, but active future development must use
> `README.md`, `docs/02_mvp_scope.md`, and `docs/10_roadmap.md`.

## 0. Назначение документа

Это рабочее техническое задание для разработки **AI Location Agent** — геоаналитической системы поддержки решений для оценки локаций под открытие ПВЗ и других франчайзинговых точек на российском рынке.

Документ предназначен для разработчика и должен использоваться как основа для проектирования архитектуры, постановки задач, подготовки документации, разработки MVP и дальнейшего расширения продукта.

---

## 1. Краткое описание продукта

**AI Location Agent** — веб-сервис, который помогает предпринимателю или аналитику оценить адрес/помещение под открытие франчайзинговой точки.

Первая версия продукта фокусируется на **ПВЗ в Краснодаре**.

Пользователь вводит адрес и параметры помещения. Система:

1. Геокодирует адрес.
2. Проверяет, что адрес относится к Краснодару / Краснодарскому краю.
3. Ищет конкурентов ПВЗ вокруг точки.
4. Считает конкурентов в радиусах 300, 500 и 700 метров.
5. Анализирует параметры помещения.
6. Считает rule-based скоринг от 0 до 100.
7. Считает confidence score.
8. Считает базовую финансовую модель.
9. Проверяет базовые требования маркетплейсов.
10. Формирует решение: `можно рассматривать`, `проверить дополнительно`, `скорее не открывать`.
11. Генерирует AI-отчёт строго на основе JSON-результатов расчёта.
12. Сохраняет результат анализа и показывает историю.

Ключевой принцип:

> Это не чат-бот, который угадывает бизнес-решения. Это геоаналитическая система, где расчёты выполняются кодом, а LLM объясняет результат, риски и ограничения.

---

## 2. Продуктовая гипотеза

На российском рынке предпринимателю сложно быстро и структурированно оценить помещение под ПВЗ или франчайзинговую точку, потому что данные разбросаны между картами, сайтами франшиз, объявлениями аренды, ручными наблюдениями и финансовыми расчётами.

Продукт должен сократить первичный анализ локации с нескольких часов/дней до 1–3 минут.

---

## 3. Целевая аудитория

### 3.1. Основной пользователь MVP

Предприниматель или менеджер, который подбирает помещение под ПВЗ в Краснодаре.

### 3.2. Вторичные пользователи

- аналитик по поиску помещений;
- инвестор/партнёр;
- владелец сети франчайзинговых точек;
- менеджер по развитию;
- пользователь, сравнивающий несколько адресов.

---

## 4. Принципы продукта

1. **Расчёты важнее генерации текста.** Скоринг, конкуренты и финансовая модель считаются кодом.
2. **LLM не является источником фактов.** LLM получает готовый JSON и формирует понятный отчёт.
3. **Все внешние данные должны иметь источник и дату обновления.**
4. **Нельзя обещать гарантированную прибыль.** Сервис даёт предварительную оценку и чек-лист ручной проверки.
5. **MVP должен быть узким и проверяемым.** Первый кейс: ПВЗ в Краснодаре.
6. **Архитектура должна быть расширяемой, но scope должен расширяться последовательно.** Активный roadmap после MVP: V1.1 validation, V1.2 compare mode, V1.3 export, V1.4 manual refresh/deltas, V1.5 scoring governance, V2 PVZ-only city-wide intelligence, V3 ML/B2B/multi-business after dataset/backtesting.

---

# 5. Версии продукта

## 5.1. MVP / Version 1.0 — анализ конкретного адреса под ПВЗ

### Цель MVP

Создать рабочий сервис, который за 1–3 минуты оценивает конкретный адрес в Краснодаре под открытие ПВЗ.

### Основной сценарий

1. Пользователь вводит адрес.
2. Пользователь вводит параметры помещения и финансовые параметры.
3. Система геокодирует адрес.
4. Система ищет конкурентов ПВЗ в радиусе 700 метров.
5. Система считает радиусы 300/500/700 м.
6. Система считает скоринг.
7. Система считает confidence score.
8. Система считает финансовую модель.
9. Система проверяет базовые требования маркетплейсов.
10. Система формирует AI-отчёт.
11. Система сохраняет анализ.
12. Пользователь видит результат, карту, конкурентов, финансы и чек-лист проверки.

### Что входит в MVP

- Ввод адреса.
- Ввод типа бизнеса, но в MVP активен только `pvz`.
- Геокодинг адреса.
- Проверка города/региона.
- Поиск конкурентов ПВЗ.
- Дедупликация конкурентов.
- Подсчёт конкурентов в радиусах 300/500/700 м.
- Расчёт rule-based скоринга 0–100.
- Расчёт confidence score.
- Расчёт финансовой модели.
- Предварительная проверка требований маркетплейсов.
- Формирование решения.
- AI-отчёт по JSON.
- История анализов.
- Просмотр детальной карточки анализа.
- Простая карта результата.
- Чек-лист ручной проверки.
- Кэширование геокодинга и данных конкурентов.
- Логирование ошибок внешних API.
- Fallback-отчёт без LLM при ошибке AI API.

### Что не входит в MVP

- Полноценный ML-прогноз выручки.
- Автоматический парсинг Авито/Циан без легального основания.
- Автономный browser-agent.
- Автоматическое инвестиционное решение.
- Поддержка всех типов бизнеса.
- Мобильное приложение.
- Сложная CRM.
- City-wide поиск лучших зон.
- H3-тепловая карта.
- Авторизация / multi-user режим.
- Трендвотчер.
- Аптеки как рабочий модуль.
- Сложная многоагентная система.
- OpenClaw-подобный автономный агент как ядро продукта.

---

## 5.2. Active post-MVP roadmap

The original V1.5/V2/V3 grouping is superseded. Use `docs/10_roadmap.md` as the
active source of truth.

### V1.1 — Stabilization, validation, documentation hardening

- Manual validation harness for 30-50 real Krasnodar addresses.
- Manual competitor checks against maps.
- Deduplication and 300/500/700 m bucket review.
- AI/fallback report hallucination review.
- Streamlit map review.
- Known limitations log.
- Fresh-clone demo reproducibility.

### V1.2 — Compare mode and decision support

- Compare 2-5 addresses.
- Unified table for score, confidence, finance, decision, and competitor counts.
- Transparent deterministic ranking.
- Saved compare sessions.
- Export comparison summary to Markdown/CSV or Excel.

### V1.3 — Export and reporting polish

- Markdown/PDF/Excel exports.
- Better report layout without changing deterministic decision logic.
- Clear assumptions and no-profit-guarantee wording.
- Fallback report remains supported.

### V1.4 — Monitoring saved locations

- Manual re-analysis of saved locations.
- Delta view between analyses.
- No background crawler and no autonomous trendwatcher.

### V1.5 — Scoring governance and marketplace rule maturity

- Scoring version comparison.
- History of scoring rule versions.
- Marketplace requirements as source-tracked/manual-check rules.
- No official marketplace compliance guarantee.

### V2 — City-wide location intelligence for PVZ only

- H3/grid-based city-wide scan.
- Heatmap and infrastructure layers.
- Batch calculation for candidate zones.
- Map-first UI.
- PVZ only; no new business types.
- No ML forecast.

### V3 — Data-driven / ML / B2B platform

- ML forecast only after dataset and backtesting.
- Backtesting, network optimization, cannibalization analysis.
- Multi-business scoring profiles.
- Auth/multi-user/roles, dashboards, integrations, observability.

### Parking Lot / Deferred

- Telegram bot.
- Mobile app.
- Browser-agent.
- Avito/Cian parsing without legal basis.
- Fully autonomous trendwatcher.
- Premature ML without dataset.
- Premature multi-business expansion.
- Premature React rewrite before Streamlit limitations are proven.

Telegram bot is not a product priority. It may be considered only as a thin
wrapper over a mature product if a real customer explicitly requests it.

---

# 6. Архитектура MVP

## 6.1. Общая схема

```text
User
  ↓
Streamlit / Web UI
  ↓
FastAPI Backend
  ↓
Application Services
  ├── Geocoding Service
  ├── Competitor Search Service
  ├── Infrastructure Service
  ├── Scoring Service
  ├── Confidence Service
  ├── Finance Service
  ├── Marketplace Requirements Service
  ├── Report Service
  └── Cache Service
  ↓
PostgreSQL + PostGIS
  ↓
External APIs
  ├── 2ГИС API
  ├── Яндекс Maps / Geocoder API
  └── OpenStreetMap / Overpass API
  ↓
LLM Provider
  ├── OpenAI API
  └── optional local Ollama provider
```

## 6.2. Рекомендуемый стек MVP

### Backend

- Python 3.11+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- PostGIS
- httpx
- tenacity
- structlog / loguru
- pytest

### Data / Geo

- PostGIS
- GeoAlchemy2
- GeoPandas для offline/исследовательских задач
- Shapely
- pyproj
- optional: H3 только для V2 PVZ-only city-wide intelligence после validation

### AI

- OpenAI API как основной provider для MVP.
- Structured JSON input для отчёта.
- Prompt versioning.
- Optional local provider:
  - Ollama;
  - `qwen3:8b`;
  - `gpt-oss:20b` для экспериментов.

### Frontend MVP

- Streamlit.

### Frontend post-MVP

- React / Next.js only if Streamlit limitations are proven, likely no earlier than V2.
- MapLibre GL / Leaflet / Яндекс Карты / 2ГИС MapGL.

### Deployment

MVP:

- Docker;
- Docker Compose;
- Render / Railway / VPS;
- PostgreSQL managed или local Docker Postgres.

Post-MVP:

- VPS / Selectel / Timeweb Cloud / Yandex Cloud;
- CI/CD;
- managed PostgreSQL;
- backup strategy.

---

# 7. Модули MVP

## 7.1. Input Module

Пользователь вводит:

```json
{
  "address": "Краснодар, улица Восточно-Кругликовская, 30",
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

Примечание: `expected_gross_income_by_user` в MVP означает пользовательскую гипотезу, а не автоматический прогноз системы.

---

## 7.2. Geocoding Module

Функции:

- получить координаты по адресу;
- нормализовать адрес;
- обработать несколько вариантов;
- проверить регион;
- сохранить результат в кэш.

Требования:

- timeout для внешнего API;
- retries с ограничением;
- логирование ошибок;
- нормальный ответ пользователю при ошибке;
- источник геокодинга сохраняется.

---

## 7.3. Competitor Search Module

Для ПВЗ искать:

- Ozon;
- Wildberries;
- Яндекс Маркет;
- СДЭК;
- Boxberry;
- Почта России;
- пункт выдачи заказов;
- постамат.

Для каждого конкурента сохранять:

- название;
- бренд;
- категория;
- адрес;
- координаты;
- расстояние;
- рейтинг;
- число отзывов;
- источник;
- external_id;
- дата обновления.

Считать:

- `competitors_300m`;
- `competitors_500m`;
- `competitors_700m`;
- `nearest_competitor_distance_m`;
- `average_competitor_distance_m`;
- `competitor_strength_score` только после V1.1 validation, если данные рейтингов/отзывов доказали полезность.

---

## 7.4. Scoring Module

MVP использует rule-based модель.

### Веса MVP для ПВЗ

```text
total_score = 
  demand_score        max 35
+ competition_score   max 25
+ rent_score          max 20
+ premises_score      max 10
+ accessibility_score max 10
```

### Demand score — 35

MVP:

- `high_density_area = true` → +15;
- `new_residential_area = true` → +15;
- базовый спрос → +5.

### Competition score — 25

Логика:

- наличие конкурентов не всегда плохо;
- конкуренты могут подтверждать спрос;
- важно оценивать насыщенность.

Пример:

- 0 конкурентов в 300 м → высокий балл;
- 1–2 конкурента в 300 м → средний балл;
- 3+ конкурента в 300 м → низкий балл;
- до 3 конкурентов в 700 м → высокий балл;
- 4–6 конкурентов в 700 м → средний балл;
- 7+ конкурентов в 700 м → низкий балл.

### Rent score — 20

Пороги MVP:

- до 60 000 ₽ → 20;
- 60 001–90 000 ₽ → 15;
- 90 001–130 000 ₽ → 8;
- выше 130 000 ₽ → 2.

Пороги должны храниться в конфигурации или таблице правил.

### Premises score — 10

Факторы:

- первый этаж;
- отдельный вход;
- площадь подходит;
- есть склад;
- можно вывеску.

### Accessibility score — 10

Факторы:

- парковка;
- остановка рядом;
- видимость;
- удобный вход;
- маршрут жителей.

---

## 7.5. Confidence Score Module

Помимо `total_score`, система считает `confidence_score` от 0 до 100.

Пример:

```text
location_score = 82/100
confidence_score = 90/100
```

Факторы снижения:

- нет прогноза валового дохода;
- данные конкурентов только из одного источника;
- нет проверки зоны маркетплейса;
- пользователь вручную отметил ключевые признаки;
- данные старше 30 дней;
- ошибка одного из внешних API.

Пример компонентов:

```text
confidence_score =
  source_completeness_score
+ freshness_score
+ manual_input_reliability_score
+ competitor_data_confidence
+ finance_data_confidence
```

Canonical MVP example:

```text
source_completeness_score:       25/25  (2 POI sources)
freshness_score:                 20/20  (< 7 days)
manual_input_reliability_score:  10/20  (ключевые поля заполнены вручную)
competitor_data_confidence:      20/20  (5 competitors found)
finance_data_confidence:         15/15  (expected income provided)
                                ------
confidence_score:                90/100
```

---

## 7.6. Finance Module

Считать:

```text
monthly_costs =
  rent
+ salary
+ taxes
+ utilities
+ internet
+ consumables
+ other_costs
+ reserve
```

```text
required_gross_income = monthly_costs + desired_profit
```

```text
net_profit = expected_gross_income_by_user - monthly_costs
```

```text
payback_months = investment / net_profit
```

Если `net_profit <= 0`, окупаемость не рассчитывается.

### Значения по умолчанию

```text
salary = 120000
taxes = 30000
utilities = 10000
internet = 5000
consumables = 10000
other_costs = 15000
reserve = 20000
desired_profit = 80000
investment = 600000
```

Все значения редактируются пользователем.

---

## 7.7. Decision Module

Решения:

```text
score >= 75 и экономика не отрицательная:
  можно рассматривать

score 60–74:
  проверить дополнительно

score < 60:
  скорее не открывать

score высокий, но net_profit <= 0:
  проверить дополнительно / скорее не открывать

аренда выше порога:
  отдельное предупреждение
```

Решение не должно формулироваться как гарантия доходности.

---

## 7.8. AI Report Module

LLM получает только структурированный JSON.

LLM обязана:

- использовать только факты из JSON;
- явно указывать недостаток данных;
- не придумывать конкурентов;
- не придумывать трафик;
- не придумывать выручку;
- не обещать прибыль;
- объяснять расчёты человеческим языком;
- выдавать чек-лист ручной проверки.

Структура отчёта:

1. Краткий вывод.
2. Итоговая оценка.
3. Решение.
4. Плюсы локации.
5. Минусы локации.
6. Конкуренция.
7. Финансовая модель.
8. Требования маркетплейса.
9. Основные риски.
10. Что проверить вручную.
11. Итоговая рекомендация.

### Fallback без LLM

Если LLM API недоступен, система возвращает:

- все расчёты;
- шаблонный отчёт;
- чек-лист ручной проверки;
- статус `report.status = "fallback"`;
- HTTP 200, если fallback-отчёт успешно создан.

Top-level ошибка `LLM_FAILED` (502) допустима только если отчёт не удалось создать вообще.

---

# 8. Модель данных

## 8.1. locations

```sql
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    address TEXT NOT NULL,
    normalized_address TEXT,
    city TEXT DEFAULT 'Краснодар',
    region TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    geom GEOGRAPHY(POINT, 4326),
    business_type TEXT NOT NULL,
    rent INTEGER,
    area_m2 NUMERIC,
    floor INTEGER,
    first_floor BOOLEAN,
    separate_entrance BOOLEAN,
    parking BOOLEAN,
    signage_possible BOOLEAN,
    storage_area BOOLEAN,
    repair_condition TEXT,
    source_url TEXT,
    geocoding_source TEXT,
    geocoding_fetched_at TIMESTAMP,
    geocoding_confidence NUMERIC,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 8.2. pois

```sql
CREATE TABLE pois (
    id SERIAL PRIMARY KEY,
    external_id TEXT,
    source TEXT NOT NULL,
    name TEXT,
    brand TEXT,
    category TEXT,
    address TEXT,
    lat DOUBLE PRECISION,
    lon DOUBLE PRECISION,
    geom GEOGRAPHY(POINT, 4326),
    rating NUMERIC,
    reviews_count INTEGER,
    fetched_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (source, external_id)
);
```

## 8.3. location_poi_distances

```sql
CREATE TABLE location_poi_distances (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    poi_id INTEGER REFERENCES pois(id),
    distance_m INTEGER,
    radius_bucket TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 8.4. scores

```sql
CREATE TABLE scores (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    scoring_version_id INTEGER,
    demand_score INTEGER,
    competition_score INTEGER,
    rent_score INTEGER,
    premises_score INTEGER,
    accessibility_score INTEGER,
    trend_score INTEGER,
    total_score INTEGER,
    confidence_score INTEGER,
    decision TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 8.5. financial_models

```sql
CREATE TABLE financial_models (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    rent INTEGER,
    salary INTEGER,
    taxes INTEGER,
    utilities INTEGER,
    internet INTEGER,
    consumables INTEGER,
    other_costs INTEGER,
    reserve INTEGER,
    desired_profit INTEGER,
    investment INTEGER,
    monthly_costs INTEGER,
    required_gross_income INTEGER,
    expected_gross_income_by_user INTEGER,
    net_profit INTEGER,
    payback_months NUMERIC,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 8.6. reports

```sql
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    report_text TEXT,
    report_json JSONB,
    provider TEXT,
    model_name TEXT,
    prompt_version TEXT,
    input_json_hash TEXT,
    temperature NUMERIC,
    tokens_input INTEGER,
    tokens_output INTEGER,
    generation_status TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 8.7. scoring_versions

В MVP таблица обязательна: каждый анализ сохраняет `scoring_version_id`. UI/admin для управления версиями, сравнение результатов между версиями и история изменений относятся к V1.5 scoring governance.

```sql
CREATE TABLE scoring_versions (
    id SERIAL PRIMARY KEY,
    business_type TEXT NOT NULL,
    version TEXT NOT NULL,
    rules JSONB NOT NULL,
    active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 8.8. marketplace_requirements

```sql
CREATE TABLE marketplace_requirements (
    id SERIAL PRIMARY KEY,
    marketplace TEXT NOT NULL,
    business_type TEXT NOT NULL,
    requirement_key TEXT NOT NULL,
    requirement_value JSONB NOT NULL,
    description TEXT,
    source_url TEXT,
    valid_from DATE,
    valid_to DATE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 8.9. trend_signals — deferred / conditional

Autonomous trendwatcher is not active V1.x scope. This table is only a possible
future option after legal, stable, useful data sources are proven.

```sql
CREATE TABLE trend_signals (
    id SERIAL PRIMARY KEY,
    business_type TEXT NOT NULL,
    city TEXT,
    area_name TEXT,
    h3_index TEXT,
    signal_type TEXT NOT NULL,
    description TEXT,
    impact TEXT,
    confidence NUMERIC,
    source TEXT,
    source_url TEXT,
    detected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

# 9. API MVP

## 9.1. POST /api/v1/analyze

Анализ адреса.

### Request

```json
{
  "address": "Краснодар, улица Восточно-Кругликовская, 30",
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

### Response

```json
{
  "location": {
    "id": 1,
    "address": "Краснодар, улица Восточно-Кругликовская, 30",
    "normalized_address": "г Краснодар, ул Восточно-Кругликовская, д 30",
    "lat": 45.000000,
    "lon": 39.000000
  },
  "competitor_counts": {
    "competitors_300m": 1,
    "competitors_500m": 3,
    "competitors_700m": 5,
    "nearest_competitor_distance_m": 180,
    "average_competitor_distance_m": 420
  },
  "score": {
    "total_score": 82,
    "confidence_score": 90,
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
    "text": "Текстовый AI-отчёт..."
  },
  "data_sources": [
    {"source": "2gis", "data_type": "geocoding", "fetched_at": "2026-05-14T10:00:00Z", "confidence": 0.95},
    {"source": "2gis", "data_type": "competitors", "fetched_at": "2026-05-14T10:00:00Z"},
    {"source": "yandex", "data_type": "competitors", "fetched_at": "2026-05-14T10:00:00Z"}
  ]
}
```

## 9.2. GET /api/v1/locations

Список проверенных адресов.

Фильтры:

- `business_type`;
- `min_score`;
- `max_score`;
- `decision`;
- `date_from`;
- `date_to`.

## 9.3. GET /api/v1/locations/{id}

Детальная карточка анализа.

## 9.4. POST /api/v1/geocode

Геокодинг адреса.

## 9.5. POST /api/v1/competitors/search

Поиск конкурентов вокруг координат.

## 9.6. POST /api/v1/report/generate

Historical planned endpoint. It is not implemented in MVP / V1.0; report
generation currently happens inside `POST /api/v1/analyze`.

## 9.7. POST /api/v1/locations/compare — V1.2

Сравнение 2–5 адресов.

---

# 10. Алгоритм анализа адреса

1. Получить входные данные.
2. Провалидировать Pydantic-схемой.
3. Нормализовать адрес.
4. Проверить кэш геокодинга.
5. Если кэша нет — вызвать внешний geocoder.
6. Если найдено несколько адресов — вернуть список вариантов.
7. Проверить город/регион.
8. Сохранить location.
9. Найти конкурентов вокруг координат.
10. Дедуплицировать конкурентов.
11. Сохранить POI.
12. Посчитать расстояния через PostGIS.
13. Посчитать конкурентов по радиусам.
14. Посчитать спрос.
15. Посчитать конкуренцию.
16. Посчитать аренду.
17. Посчитать помещение.
18. Посчитать доступность.
19. Посчитать total_score.
20. Посчитать confidence_score.
21. Рассчитать финансовую модель.
22. Проверить требования маркетплейсов.
23. Определить решение.
24. Сформировать JSON анализа.
25. Передать JSON в AI-модуль.
26. Если AI недоступен — сформировать fallback-отчёт.
27. Сохранить отчёт.
28. Вернуть пользователю результат.

---

# 11. Интерфейс MVP

## 11.1. Главная страница

Поля:

- адрес;
- тип бизнеса;
- аренда;
- площадь;
- этаж;
- первый этаж;
- отдельный вход;
- парковка;
- возможность вывески;
- складская зона;
- состояние ремонта;
- новый ЖК / район активной застройки;
- высокая плотность жилья;
- остановка рядом;
- хорошая видимость;
- ожидаемый валовый доход пользователя;
- инвестиции;
- желаемая прибыль.

Кнопка:

- `Проанализировать`.

## 11.2. Страница результата

Блоки:

- итоговый score;
- confidence score;
- решение;
- карта;
- список конкурентов;
- финансовая модель;
- требования маркетплейсов;
- AI-отчёт;
- чек-лист ручной проверки;
- предупреждения;
- дата обновления данных;
- источники данных.

## 11.3. История анализов

Таблица:

- дата;
- адрес;
- тип бизнеса;
- аренда;
- total score;
- confidence score;
- решение;
- минимальный нужный доход;
- прогнозная чистая прибыль;
- окупаемость.

Фильтры:

- по району;
- по баллу;
- по решению;
- по типу бизнеса;
- по дате.

---

# 12. Чек-лист ручной проверки ПВЗ

Система должна всегда выдавать чек-лист:

1. Проверить фактическую проходимость утром, днём и вечером.
2. Проверить возможность размещения вывески.
3. Проверить договор аренды.
4. Проверить арендные каникулы.
5. Проверить скрытые коммунальные платежи.
6. Проверить состояние входной группы.
7. Проверить возможность подъезда курьеров.
8. Проверить конкурентов вручную в 2ГИС/Яндекс Картах.
9. Проверить отзывы конкурентов.
10. Проверить требования конкретного маркетплейса.
11. Проверить зону на карте Ozon/WB/Яндекс Маркета.
12. Проверить соответствие площади и склада.
13. Проверить нежелательное соседство.
14. Проверить интернет.
15. Проверить электричество.
16. Проверить видеонаблюдение.
17. Проверить условия расторжения договора аренды.
18. Проверить доступность для клиентов с колясками и маломобильных клиентов.
19. Проверить, нет ли сильного конкурента в соседнем дворе/на другой стороне дороги.
20. Проверить видимость точки с основных пешеходных маршрутов.

---

# 13. Безопасность и юридические ограничения

## 13.1. Безопасность

- API-ключи только в `.env` / secret storage.
- Ключи не отправлять на frontend.
- Rate limiting.
- Авторизация и роли относятся к V3, не к MVP.
- Логирование действий пользователей.
- Timeout для всех внешних запросов.
- Retry policy.
- Sanitization пользовательского ввода.
- Не давать LLM доступ к shell, БД или секретам.
- Не использовать автономный browser-agent в MVP.

## 13.2. Юридические ограничения

- Не парсить сайты недвижимости без проверки правил площадки.
- Для MVP использовать ручной ввод аренды или легальные API/выгрузки.
- Указывать источник данных.
- Не выдавать отчёт как юридическую/финансовую гарантию.
- Для аптек и других новых бизнесов в V3 нужен отдельный юридический блок.

---

# 14. Тестирование

## 14.1. Unit tests

Покрыть:

- scoring;
- finance;
- decision module;
- confidence score;
- marketplace requirements;
- geocoding parser;
- competitor deduplication.

## 14.2. Integration tests

Покрыть:

- `/api/v1/analyze`;
- `/api/v1/geocode`;
- `/api/v1/competitors/search`;
- report generation through `/api/v1/analyze` fallback/LLM flow;
- сохранение анализа в БД;
- fallback при ошибке AI;
- `LLM_FAILED` 502 только если отчёт не удалось создать вообще;
- fallback при ошибке внешнего API.

## 14.3. Manual validation

Проверить 30–50 адресов Краснодара:

- сравнить автоматический анализ с ручным;
- проверить дубли конкурентов;
- проверить адекватность весов;
- проверить корректность финансов;
- проверить качество AI-отчётов.

---

# 15. Критерии приёмки MVP

MVP считается готовым, если:

1. Пользователь может ввести адрес в Краснодаре.
2. Система получает координаты.
3. Система обрабатывает несколько вариантов адреса.
4. Система находит конкурентов ПВЗ.
5. Система считает конкурентов в 300/500/700 м.
6. Система сохраняет конкурентов с источником и датой обновления.
7. Система считает rule-based score.
8. Система считает confidence score.
9. Система считает финансовую модель.
10. Система выдаёт решение.
11. Система показывает предупреждения.
12. Система генерирует AI-отчёт.
13. Если AI недоступен, система возвращает fallback-отчёт.
14. Система сохраняет анализ.
15. Пользователь может открыть историю анализов.
16. Пользователь может открыть детальную карточку анализа.
17. Есть базовая карта.
18. Есть чек-лист ручной проверки.
19. Есть unit tests для scoring и finance.
20. README объясняет запуск проекта.

---

# 16. Рекомендуемый roadmap разработки

This historical section is superseded by `docs/10_roadmap.md`. The active
post-MVP sequence is:

1. **V1.1** — stabilization, validation, documentation hardening.
2. **V1.2** — compare mode and decision support.
3. **V1.3** — export and reporting polish.
4. **V1.4** — manual refresh and deltas for saved locations.
5. **V1.5** — scoring governance and marketplace rule maturity.
6. **V2** — city-wide location intelligence for PVZ only.
7. **V3** — data-driven / ML / B2B / multi-business platform after dataset and
   backtesting.

Deferred ideas must not be treated as active roadmap: Telegram bot, mobile app,
browser-agent, unsupported Avito/Cian parsing, autonomous trendwatcher,
premature ML, premature multi-business expansion, and premature React rewrite.

Telegram bot is not a product priority. It may be considered only as a thin
wrapper over a mature product if a real customer explicitly requests it.

---

# 17. Документация проекта для портфолио

В репозитории желательно иметь:

```text
docs/
  product/
    product_requirements.md
    user_flows.md
    roadmap.md
  architecture/
    architecture_overview.md
    data_model.md
    api_contract.md
    deployment.md
  methodology/
    scoring_methodology.md
    financial_model.md
    confidence_score.md
    data_sources.md
  ai/
    ai_report_generation.md
    prompt_versions.md
    llm_guardrails.md
  validation/
    test_plan.md
    manual_validation_checklist.md
    sample_reports.md
```

README должен включать:

- краткое описание;
- business value;
- features;
- architecture diagram;
- tech stack;
- quick start;
- demo screenshots;
- API examples;
- limitations;
- roadmap;
- portfolio notes.

---

# 18. Финальный принцип разработки

Сначала построить надёжное ядро:

```text
address → data → scoring → finance → report
```

Затем расширять:

```text
validation → compare → export → manual refresh → scoring governance → PVZ city-wide intelligence → dataset/backtesting → ML forecast
```

Не начинать с автономных агентов, сложного ML или полного парсинга интернета. Это должно быть инженерно контролируемое решение, где каждый вывод можно объяснить, воспроизвести и проверить.
