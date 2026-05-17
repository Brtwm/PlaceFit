# Финансовая модель — PlaceFit MVP

## Принцип

Простая детерминированная модель break-even и payback. Не прогнозирует выручку. Показывает, сколько нужно зарабатывать для окупаемости.

## Формулы

```
monthly_costs = rent + salary + taxes + utilities + internet + consumables + other_costs + reserve

required_gross_income = monthly_costs + desired_profit

net_profit = expected_gross_income_by_user - monthly_costs

payback_months = investment / net_profit    (только если net_profit > 0)
```

## Значения по умолчанию

| Параметр | Значение (₽) | Редактируемый |
|----------|-------------|---------------|
| salary | 120 000 | Да |
| taxes | 30 000 | Да |
| utilities | 10 000 | Да |
| internet | 5 000 | Да |
| consumables | 10 000 | Да |
| other_costs | 15 000 | Да |
| reserve | 20 000 | Да |
| desired_profit | 80 000 | Да |
| investment | 600 000 | Да |

Все значения пользователь может менять в UI. Дефолты подобраны для типичного ПВЗ в Краснодаре.

## Логика расчёта

### Пример 1: income указан

```
rent = 85 000
monthly_costs = 85000 + 120000 + 30000 + 10000 + 5000 + 10000 + 15000 + 20000 = 295 000
required_gross_income = 295000 + 80000 = 375 000
expected_gross_income_by_user = 360 000
net_profit = 360000 - 295000 = 65 000
investment = 600 000
payback_months = 600000 / 65000 = 9.2 мес
```

### Пример 2: income не указан

```
monthly_costs = 295 000
required_gross_income = 375 000
net_profit = null (не рассчитывается)
payback_months = null
```

В этом случае отчёт показывает: «Для выхода на желаемую прибыль нужен валовый доход не менее 375 000 ₽/мес».

### Пример 3: отрицательная прибыль

```
expected_gross_income_by_user = 200 000
monthly_costs = 295 000
net_profit = -95 000
payback_months = null (не рассчитывается при net_profit ≤ 0)
```

Предупреждение: «При указанном доходе точка убыточна».

## Влияние на decision

| Условие | Эффект на решение |
|---------|-------------------|
| net_profit > 0 | Не влияет негативно |
| net_profit ≤ 0 | Понижает до «проверить» или «не открывать» |
| net_profit = null | Не влияет (данных нет) |
| rent > 130 000 | Отдельное предупреждение |

## Ограничения

1. **Не прогнозирует выручку.** `expected_gross_income_by_user` — гипотеза пользователя.
2. **Дефолты примерные.** Реальные расходы могут отличаться.
3. **Нет сезонности.** Модель считает среднемесячно.
4. **Нет учёта роста.** Первые месяцы дохода обычно ниже среднего.
5. **Нет налоговой оптимизации.** Taxes = фиксированная сумма.

## Будущее (V3)

- ML-прогноз `expected_gross_income` на основе features (локация, конкуренты, плотность).
- Сценарный анализ (optimistic / base / pessimistic).
- Учёт сезонности.
- ROI и NPV.
