# PlaceFit — геоаналитика для выбора локации ПВЗ

PlaceFit — система поддержки решений для оценки коммерческих локаций под пункты выдачи заказов. MVP фокусируется на одном сценарии: анализ конкретного адреса в Краснодаре под ПВЗ.

> Статус проекта: MVP implementation is in staged progress. Backend skeleton, schemas, deterministic core, and database layer are implemented up to the current phase; UI, providers, and report orchestration are still planned.

## Проблема

Предпринимателю, выбирающему помещение под ПВЗ, приходится вручную собирать данные о конкурентах, считать финансы в таблицах и сверять требования маркетплейсов. Такой анализ занимает часы или дни, зависит от субъективной оценки и легко теряет важные ограничения.

## Решение

PlaceFit должен за 1–3 минуты дать структурированную оценку адреса:

- конкуренты в радиусах 300/500/700 м;
- rule-based score 0–100 по спросу, конкуренции, аренде, помещению и доступности;
- confidence score 0–100 для оценки надёжности данных;
- финансовая модель с monthly costs, break-even и payback;
- AI-отчёт строго по подготовленному JSON;
- fallback-отчёт, если LLM недоступен;
- чек-лист ручной проверки перед принятием решения.

Ключевой принцип: **«AI объясняет, код считает»**. Scoring, finance, decision и confidence рассчитываются детерминированным backend code. LLM только превращает готовый JSON в человеко-читаемый отчёт.

## Архитектура MVP

```text
User → Streamlit UI → FastAPI Backend → Services → PostgreSQL/PostGIS
                                            ↓
                                      External APIs
                                  2GIS / Yandex / OSM
                                            ↓
                                      LLM Provider
                                  OpenAI → fallback
```

Основные архитектурные решения:

- provider abstraction для внешних API;
- PostgreSQL/PostGIS для хранения адресов, POI и расчёта расстояний;
- scoring versioning через `scoring_versions` и `scoring_version_id`;
- marketplace checks в MVP возвращают `needs_manual_check`, без утверждения юридически точного соответствия требованиям;
- LLM не получает доступ к БД, API, shell или секретам.

## Стек

- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x.
- **Database**: PostgreSQL 15+ с PostGIS.
- **Frontend MVP**: Streamlit.
- **Geodata**: 2GIS API, Yandex Maps, OpenStreetMap/Overpass fallback.
- **AI**: OpenAI API для отчётов, template fallback.
- **Testing**: pytest, fixtures, mocked external APIs.
- **DevOps planned**: Docker, Docker Compose.

## MVP Scope

Входит:

- один город: Краснодар;
- один бизнес-тип: ПВЗ;
- один адрес за анализ;
- карта и таблица конкурентов;
- история анализов;
- детерминированные scoring/finance/confidence/decision модули;
- AI report из prepared JSON и fallback report.

Не входит:

- ML-прогноз выручки;
- city-wide search, H3 и heatmap;
- trendwatcher;
- Telegram-бот;
- авторизация и multi-user режим;
- парсинг Авито/Циан;
- поддержка других типов бизнеса.

## Planned Quick Start

Команды ниже описывают целевой сценарий после реализации MVP. Сейчас они не являются рабочей инструкцией запуска.

```bash
git clone https://github.com/Brtwm/PlaceFit.git
cd PlaceFit
cp .env.example .env
# Заполнить API ключи в .env
# docker-compose up --build
# Открыть Streamlit UI после появления backend/frontend кода
```

## Документация

- [Product overview](docs/00_overview.md)
- [MVP scope](docs/02_mvp_scope.md)
- [Architecture](docs/03_architecture.md)
- [Data model](docs/04_data_model.md)
- [API contract](docs/05_api_contract.md)
- [Scoring model](docs/06_scoring_model.md)
- [Financial model](docs/07_financial_model.md)
- [AI report](docs/08_ai_report.md)
- [Testing strategy](docs/09_testing_strategy.md)
- [Roadmap](docs/10_roadmap.md)
- [Marketplace requirements](docs/12_marketplace_requirements.md)
- [Codex MVP coding plan](docs/13_coding_plan_for_codex_mvp.md)

## Roadmap

| Версия | Фокус |
|--------|-------|
| MVP | Один адрес, ПВЗ, Краснодар, deterministic analysis |
| V1.5 | Сравнение адресов, экспорт, мониторинг, scoring admin/version comparison |
| V2 | City-wide search, H3-карта, trendwatcher, infrastructure intelligence |
| V3 | ML-прогноз, multi-business, B2B platform, auth/roles |

## Ограничения

- PlaceFit не гарантирует прибыль и не является финансовой рекомендацией.
- `expected_gross_income_by_user` — гипотеза пользователя, не прогноз системы.
- Требования маркетплейсов в MVP требуют ручной проверки по официальным источникам.
- Качество результата зависит от свежести и полноты внешних геоданных.

## License

MIT License. See [LICENSE](LICENSE).
