# Data Model — PlaceFit

## СУБД

PostgreSQL 15+ с расширением PostGIS 3.x.

## MVP таблицы

### locations
Основная таблица — анализируемые адреса.

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
    business_type TEXT NOT NULL DEFAULT 'pvz',
    rent INTEGER,
    area_m2 NUMERIC,
    floor INTEGER,
    first_floor BOOLEAN,
    separate_entrance BOOLEAN,
    parking BOOLEAN,
    signage_possible BOOLEAN,
    storage_area BOOLEAN,
    repair_condition TEXT,        -- 'good', 'normal', 'needs_repair'
    new_residential_area BOOLEAN,
    high_density_area BOOLEAN,
    bus_stop_nearby BOOLEAN,
    good_visibility BOOLEAN,
    source_url TEXT,
    geocoding_source TEXT,       -- '2gis', 'yandex', 'osm'
    geocoding_fetched_at TIMESTAMP,
    geocoding_confidence NUMERIC,
    user_id INTEGER,             -- reserved for future auth/multi-user mode, not used in MVP
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_locations_geom ON locations USING GIST(geom);
CREATE INDEX idx_locations_city ON locations(city);
CREATE INDEX idx_locations_business_type ON locations(business_type);
```

### pois
Точки интереса — конкуренты ПВЗ.

```sql
CREATE TABLE pois (
    id SERIAL PRIMARY KEY,
    external_id TEXT,
    source TEXT NOT NULL,         -- '2gis', 'yandex', 'osm'
    name TEXT,
    brand TEXT,                   -- 'ozon', 'wildberries', 'yandex_market', 'cdek', 'boxberry', 'pochta'
    category TEXT,                -- 'pvz', 'postamat'
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

CREATE INDEX idx_pois_geom ON pois USING GIST(geom);
CREATE INDEX idx_pois_brand ON pois(brand);
```

### location_poi_distances
Расстояния от location до конкурентов.

```sql
CREATE TABLE location_poi_distances (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id) ON DELETE CASCADE,
    poi_id INTEGER REFERENCES pois(id) ON DELETE CASCADE,
    distance_m INTEGER NOT NULL,
    radius_bucket TEXT,           -- '300m', '500m', '700m'
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lpd_location ON location_poi_distances(location_id);
```

### scores
Результаты скоринга.

```sql
CREATE TABLE scores (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id) ON DELETE CASCADE,
    scoring_version_id INTEGER REFERENCES scoring_versions(id),
    demand_score INTEGER,
    competition_score INTEGER,
    rent_score INTEGER,
    premises_score INTEGER,
    accessibility_score INTEGER,
    total_score INTEGER,
    confidence_score INTEGER,
    decision TEXT,                -- 'можно рассматривать', 'проверить дополнительно', 'скорее не открывать'
    details JSONB,               -- подробные breakdown
    created_at TIMESTAMP DEFAULT NOW()
);
```

### financial_models
Результаты финансовой модели.

```sql
CREATE TABLE financial_models (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id) ON DELETE CASCADE,
    rent INTEGER,
    salary INTEGER DEFAULT 120000,
    taxes INTEGER DEFAULT 30000,
    utilities INTEGER DEFAULT 10000,
    internet INTEGER DEFAULT 5000,
    consumables INTEGER DEFAULT 10000,
    other_costs INTEGER DEFAULT 15000,
    reserve INTEGER DEFAULT 20000,
    desired_profit INTEGER DEFAULT 80000,
    investment INTEGER DEFAULT 600000,
    monthly_costs INTEGER,
    required_gross_income INTEGER,
    expected_gross_income_by_user INTEGER,
    net_profit INTEGER,
    payback_months NUMERIC,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### reports
AI-отчёты.

```sql
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id) ON DELETE CASCADE,
    report_text TEXT,
    report_json JSONB,
    provider TEXT,               -- 'openai', 'fallback'
    model_name TEXT,             -- 'gpt-4o-mini', etc
    prompt_version TEXT,         -- 'v1.0'
    input_json_hash TEXT,        -- для дедупликации
    temperature NUMERIC,
    tokens_input INTEGER,
    tokens_output INTEGER,
    generation_status TEXT,      -- 'success', 'failed', 'fallback'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### scoring_versions
Версии правил скоринга.

В MVP таблица обязательна: каждый анализ сохраняет `scoring_version_id`. Управление версиями через UI/admin, сравнение результатов между версиями и история изменений относятся к V1.5.

```sql
CREATE TABLE scoring_versions (
    id SERIAL PRIMARY KEY,
    business_type TEXT NOT NULL,
    version TEXT NOT NULL,        -- 'v1.0'
    rules JSONB NOT NULL,
    active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### marketplace_requirements
Требования маркетплейсов (справочник).

```sql
CREATE TABLE marketplace_requirements (
    id SERIAL PRIMARY KEY,
    marketplace TEXT NOT NULL,    -- 'ozon', 'wildberries', 'yandex_market'
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

## Будущие таблицы (НЕ MVP)

### trend_signals (V2)
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

## Заметки

1. **PostGIS GEOGRAPHY vs GEOMETRY**: используем GEOGRAPHY(POINT, 4326) для корректных метрических расстояний (ST_Distance возвращает метры).
2. **Дедупликация POI**: UNIQUE constraint по (source, external_id). Кросс-источниковая дедупликация — по расстоянию (< 50 м) + совпадению бренда.
3. **Source freshness**: `locations.geocoding_fetched_at` и `pois.fetched_at`. Данные старше TTL перезапрашиваются.
4. **API `data_sources`**: вычисляется из `locations.geocoding_source`, `locations.geocoding_fetched_at`, `locations.geocoding_confidence`, `pois.source`, `pois.fetched_at` и `reports.provider`.
5. **В будущем**: не дублировать конкурентов per location. POI — глобальный справочник. Связь через `location_poi_distances`.
