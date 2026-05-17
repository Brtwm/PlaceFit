# Trendwatcher — будущий модуль (V2)

## Почему не MVP

1. Нет стабильных источников данных для мониторинга.
2. Требует cron/scheduler для периодического сбора.
3. Требует значительной инфраструктуры (очереди, хранение сигналов).
4. MVP фокус — оценка конкретного адреса, не мониторинг трендов.

## Назначение

Trendwatcher **не принимает решений**. Он собирает сигналы из внешних источников и превращает их в структурированные признаки, которые дополняют scoring.

## Источники сигналов

| Источник | Тип сигнала | Сложность |
|----------|------------|-----------|
| 2ГИС / Яндекс / OSM | Открытие/закрытие конкурентов | Средняя |
| Отзывы конкурентов | Проблемы с обслуживанием | Средняя |
| Новости маркетплейсов | Изменение условий Ozon/WB | Низкая |
| Данные о новых ЖК | Рост спроса в районе | Средняя |
| Поисковый спрос | Yandex Wordstat по району | Высокая |
| Локальные новости | Инфраструктурные изменения | Высокая |
| Ручные наблюдения | Пользовательский input | Низкая |

## Модель данных

```sql
-- Уже определена в data_model.md как V2 таблица
CREATE TABLE trend_signals (
    id SERIAL PRIMARY KEY,
    business_type TEXT NOT NULL,
    city TEXT,
    area_name TEXT,
    h3_index TEXT,
    signal_type TEXT NOT NULL,
    description TEXT,
    impact TEXT,          -- 'positive_for_new_entry', 'negative_for_new_entry', 'neutral'
    confidence NUMERIC,   -- 0.0 - 1.0
    source TEXT,
    source_url TEXT,
    detected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## trend_score

```
trend_score = weighted_sum(signal_impacts) normalized to 0-100
```

Влияет на zone_score в city-wide search, но НЕ на location_score в MVP.

## Пример сигнала

```json
{
  "signal_type": "competitor_closed",
  "business_type": "pvz",
  "area": "Краснодар, ЮМР",
  "description": "Wildberries на ул. Героев Разведчиков закрылся (по данным 2ГИС)",
  "impact": "positive_for_new_entry",
  "confidence": 0.85,
  "source": "2gis_monitoring",
  "detected_at": "2026-05-10"
}
```

## Мониторинг (V1.5 → V2)

- V1.5: ручной мониторинг сохранённых адресов (перезапуск анализа).
- V2: автоматический мониторинг с алертами при значимых изменениях.
