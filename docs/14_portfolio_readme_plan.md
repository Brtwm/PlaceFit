# Portfolio README Plan — PlaceFit

## Структура README

````markdown
# PlaceFit — Location Intelligence для ПВЗ

[краткое описание, 2-3 предложения]

## 🎯 Проблема
[описание боли пользователя]

## 💡 Решение
[что делает PlaceFit, ключевая ценность]

## 🖼️ Screenshots
[3-5 скриншотов: ввод, результат, карта, отчёт, история]

## ⚡ Ключевые возможности
- Rule-based scoring 0–100
- Confidence score
- Автоматический поиск конкурентов
- Финансовая модель
- AI-отчёт с guardrails
- Чек-лист ручной проверки

## 🏗️ Архитектура
[диаграмма: User → Streamlit → FastAPI → Services → DB → APIs]

## 🛠️ Стек
Python, FastAPI, PostgreSQL/PostGIS, Streamlit, OpenAI API, Docker

## 🚀 Quick Start
```bash
git clone ...
cp .env.example .env
docker-compose up
```

## 📊 Пример результата
[JSON или скриншот одного анализа]

## 📋 API
[2-3 основных endpoint с кратким описанием]

## 🗺️ Roadmap
MVP → V1.5 (сравнение, Telegram) → V2 (H3, trendwatcher) → V3 (ML)

## ⚠️ Ограничения
- MVP: только ПВЗ, только Краснодар
- Не прогнозирует выручку автоматически
- Не заменяет ручную проверку
- AI не является источником фактов

## 📖 Документация
[ссылки на docs/]

## 📝 Лицензия
````

## Скриншоты/диаграммы для подготовки

1. **Input form** — Streamlit форма ввода адреса.
2. **Result dashboard** — Score card + decision.
3. **Competitor map** — Карта с маркерами конкурентов.
4. **AI report** — Пример текста отчёта.
5. **History page** — Таблица анализов.
6. **Architecture diagram** — Mermaid или draw.io.

## Чего НЕ стоит делать в README

- ❌ Overclaim: «автоматически найдёт лучшую локацию».
- ❌ «AI принимает бизнес-решения».
- ❌ «Гарантированная прибыль».
- ❌ Скрывать ограничения.
- ❌ Показывать только успешные кейсы.

## Portfolio value signals

- Продуктовое мышление (не просто код, а business problem → solution).
- Архитектурная зрелость (provider abstraction, scoring versioning).
- Честность (confidence score, limitations, чек-лист).
- Тестируемость (unit tests, mock strategy).
- DevOps (Docker, docker-compose, .env).
- AI инженерия (structured input, hallucination prevention, fallback).
