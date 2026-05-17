# Стратегия тестирования — PlaceFit MVP

## Unit tests

### scoring.py
```
test_demand_score_all_true → 35
test_demand_score_all_false → 5
test_demand_score_partial → 20
test_competition_score_no_competitors → 25
test_competition_score_many_close → low
test_rent_score_cheap → 20
test_rent_score_expensive → 2
test_premises_score_ideal → 10
test_premises_score_bad_floor → score без first_floor бонуса
test_accessibility_score_full → 10
test_total_score_range_0_100 → parameterized
test_total_score_deterministic → одинаковый ввод = одинаковый score
```

### finance.py
```
test_monthly_costs_default → 295000
test_monthly_costs_custom → правильная сумма
test_required_gross_income → costs + desired_profit
test_net_profit_positive → income - costs
test_net_profit_negative → отрицательное число
test_net_profit_no_income → null
test_payback_positive → investment / net_profit
test_payback_negative_profit → null
test_payback_zero_profit → null
```

### decision.py
```
test_decision_high_score_positive_profit → «можно рассматривать»
test_decision_mid_score → «проверить дополнительно»
test_decision_low_score → «скорее не открывать»
test_decision_high_score_negative_profit → «проверить дополнительно»
test_decision_high_rent_warning → предупреждение
```

### confidence.py
```
test_confidence_full_data → high score
test_confidence_one_source → снижение
test_confidence_old_data → снижение
test_confidence_no_income → снижение
test_confidence_no_competitors_found → снижение
```

### deduplication
```
test_dedup_same_external_id → 1 result
test_dedup_close_distance_same_brand → 1 result
test_dedup_different_brands_close → 2 results
test_dedup_same_brand_far → 2 results
```

### geocoding parser
```
test_parse_2gis_response → корректные координаты
test_parse_yandex_response → корректные координаты
test_city_validation_krasnodar → pass
test_city_validation_moscow → fail
test_multiple_results → список вариантов
```

## Integration tests

### /api/v1/analyze (с моками внешних API)
```
test_analyze_success → 200, полный response
test_analyze_geocoding_fail → 502, error
test_analyze_city_not_supported → 400, error
test_analyze_ambiguous_address → 400, suggestions
test_analyze_llm_fail_fallback → 200, report.status = "fallback"
test_analyze_llm_and_fallback_fail → 502, error.code = "LLM_FAILED"
test_analyze_saves_to_db → location + score + finance + report в БД
test_analyze_validation_error → 422, missing required fields
```

### /api/v1/locations
```
test_locations_list → 200, items
test_locations_filter_by_score → filtered results
test_locations_filter_by_decision → filtered results
test_locations_detail → 200, full analysis
test_locations_not_found → 404
```

## Mock strategy

Внешние API (2GIS, Yandex, OpenAI) мокаются через:
- `pytest fixtures` с JSON responses
- `httpx` mock transport
- Реальные API **не** вызываются в CI

Файлы fixtures:
```
tests/fixtures/
├── geocoding/
│   ├── 2gis_success.json
│   ├── 2gis_ambiguous.json
│   └── yandex_success.json
├── competitors/
│   ├── 2gis_competitors_5.json
│   ├── 2gis_competitors_0.json
│   └── duplicates.json
└── llm/
    ├── openai_success.json
    └── openai_error.json
```

## AI report validation

```
test_report_json_schema → input JSON validates against schema
test_report_contains_required_sections → все 9 секций присутствуют
test_fallback_report_format → шаблон корректен
test_report_no_hallucinated_competitors → report не содержит имён, которых нет в input
```

## Manual validation

После запуска MVP — проверка 30–50 реальных адресов Краснодара:

1. Проверить конкурентов на карте 2ГИС вручную — совпадает ли с автоматическим поиском.
2. Проверить дедупликацию — нет ли дублей.
3. Оценить адекватность score — сравнить с ручной оценкой.
4. Проверить финансовую модель — корректные суммы.
5. Прочитать AI-отчёты — нет ли галлюцинаций.
6. Зафиксировать результаты в таблице.

## Команды

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# All tests
pytest -v --tb=short

# Coverage
pytest --cov=app --cov-report=html
```
