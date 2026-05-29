# AI Report — PlaceFit MVP

## Роль AI

LLM **объясняет результаты расчётов** человеческим языком. LLM **не является источником фактов**. Все числа, конкуренты, score, финансы — из JSON.

MVP использует OpenAI-compatible provider abstraction. Конкретный runtime-provider задаётся через `.env`; LLM по умолчанию выключен, а fallback report должен работать без LLM API key.

Fallback report is a first-class successful response. It is not an error state
when LLM is disabled, no LLM key is configured, or the LLM provider is
unavailable but the deterministic fallback report succeeds.

## JSON input contract

LLM получает structured JSON (результат полного анализа):

```json
{
  "location": {
    "address": "г Краснодар, ул Восточно-Кругликовская, д 30",
    "lat": 45.035, "lon": 39.028,
    "business_type": "pvz",
    "rent": 85000, "area_m2": 35,
    "first_floor": true, "separate_entrance": true,
    "parking": true, "storage_area": true,
    "repair_condition": "normal",
    "new_residential_area": true, "high_density_area": true,
    "bus_stop_nearby": true, "good_visibility": true
  },
  "competitors": {
    "competitors_300m": 1, "competitors_500m": 3, "competitors_700m": 5,
    "nearest_competitor_distance_m": 180,
    "average_competitor_distance_m": 420,
    "list": [
      {"name": "Ozon", "brand": "ozon", "distance_m": 180, "rating": 4.2, "reviews_count": 156}
    ]
  },
  "score": {
    "total_score": 82, "confidence_score": 90,
    "decision": "можно рассматривать",
    "details": {"demand_score": 35, "competition_score": 12, "rent_score": 15, "premises_score": 10, "accessibility_score": 10}
  },
  "finance": {
    "monthly_costs": 295000, "required_gross_income": 375000,
    "expected_gross_income_by_user": 360000,
    "net_profit": 65000, "payback_months": 9.2
  },
  "marketplace_requirements": {
    "ozon": {
      "status": "needs_manual_check",
      "needs_manual_check": true,
      "manual_checks": ["Проверить зону открытия на официальном сайте Ozon"],
      "warning": "Требования маркетплейсов нужно сверить с официальными источниками."
    }
  },
  "data_sources": [
    {"source": "2gis", "data_type": "geocoding", "fetched_at": "2026-05-14", "confidence": 0.95},
    {"source": "2gis", "data_type": "competitors", "fetched_at": "2026-05-14"},
    {"source": "yandex", "data_type": "competitors", "fetched_at": "2026-05-14"}
  ]
}
```

## Структура отчёта

1. **Краткий вывод** (2–3 предложения).
2. **Итоговая оценка** (score / confidence / решение).
3. **Плюсы локации**.
4. **Минусы и риски**.
5. **Конкуренция** (анализ конкурентов по радиусам).
6. **Финансовая модель** (объяснение расчётов).
7. **Требования маркетплейсов**.
8. **Что проверить вручную** (чек-лист).
9. **Итоговая рекомендация**.

## Hallucination prevention rules

В системном промпте зафиксировано:

1. ❌ Не придумывай конкурентов, которых нет в JSON.
2. ❌ Не придумывай пешеходный трафик.
3. ❌ Не придумывай выручку.
4. ❌ Не обещай прибыль или гарантию успеха.
5. ❌ Не указывай данные, которых нет в JSON.
6. ✅ Если данных недостаточно — явно скажи об этом.
7. ✅ Используй только числа из JSON.
8. ✅ Укажи confidence_score и объясни, почему он такой.
9. ✅ Дай чек-лист ручной проверки.

## Prompt template (v1.0)

```
SYSTEM:
Ты — аналитик по коммерческой недвижимости. Ты получаешь JSON с результатами
автоматического анализа локации под пункт выдачи заказов (ПВЗ).

Твоя задача — написать структурированный отчёт на основе ТОЛЬКО предоставленных данных.

Правила:
- Используй ТОЛЬКО факты из JSON. Не добавляй информацию, которой нет.
- Если данных недостаточно для вывода — явно укажи это.
- Не обещай прибыль и не гарантируй успех бизнеса.
- Не придумывай конкурентов, трафик, выручку.
- Объясняй расчёты простым языком.
- Укажи ограничения анализа.
- Завершай чек-листом ручной проверки.

Формат отчёта:
## Краткий вывод
## Итоговая оценка
## Плюсы локации
## Минусы и риски
## Конкуренция
## Финансовая модель
## Требования маркетплейсов
## Что проверить вручную
## Итоговая рекомендация

USER:
Вот результаты анализа локации в формате JSON:

{analysis_json}

Напиши структурированный отчёт.
```

## Параметры генерации

### Runtime configuration

```text
LLM_ENABLED=false
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
```

Если пользователь хочет использовать NeuralDeep Hub или другой OpenAI-compatible endpoint, он заполняет `LLM_BASE_URL`, `LLM_API_KEY` и `LLM_MODEL` по актуальной документации выбранного provider-а. NeuralDeep Hub не является обязательной зависимостью MVP.

| Параметр | Значение |
|----------|----------|
| provider | `openai_compatible` |
| model | задаётся через `LLM_MODEL` |
| temperature | 0.3 |
| max_tokens | 2000 |

## Fallback без LLM

Если `LLM_ENABLED=false`, LLM API key не задан или LLM API недоступен:

```
Автоматический отчёт (AI-модуль временно недоступен)

Итоговая оценка: {total_score}/100
Уверенность: {confidence_score}/100
Решение: {decision}

Компоненты оценки:
- Спрос: {demand_score}/35
- Конкуренция: {competition_score}/25
- Аренда: {rent_score}/20
- Помещение: {premises_score}/10
- Доступность: {accessibility_score}/10

Конкуренты: {competitors_300m} в 300м, {competitors_500m} в 500м, {competitors_700m} в 700м
Ближайший: {nearest_competitor_distance_m} м

Финансы:
- Ежемесячные расходы: {monthly_costs} ₽
- Необходимый доход: {required_gross_income} ₽
- Чистая прибыль: {net_profit} ₽
- Окупаемость: {payback_months} мес

Для AI-отчёта от подключённого LLM provider повторите анализ позже или включите
LLM в `.env`.
```

Статус в response: `"status": "fallback"`.

При успешном fallback endpoint возвращает HTTP 200. Ошибка `LLM_FAILED` (502) допустима только если отчёт не удалось создать вообще.

## Prompt versioning

- Версия хранится в `reports.prompt_version`.
- При изменении промпта — новая версия (v1.1, v2.0).
- Старые отчёты сохраняют привязку к старой версии.
