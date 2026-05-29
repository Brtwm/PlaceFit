# Marketplace Requirements — PlaceFit

## Concept

Marketplaces such as Ozon, Wildberries, and Yandex Market have operational
requirements for pickup points. PlaceFit can help the user remember what to
verify, but it must not claim official compliance.

In MVP / V1.0 all marketplace checks return `needs_manual_check`.

## MVP Behavior

MVP does not produce `passed` or `failed` marketplace compliance decisions.

Reasons:

- Requirements change.
- Opening zones are checked on marketplace-owned systems.
- Legal and operational terms can be individual.
- The project does not store verified official rules yet.

MVP response includes only:

- `ozon`;
- `wildberries`;
- `yandex_market`.

Other pickup networks can appear as POI/competitors, but they are not MVP
marketplace requirement modules.

## Required Wording

Use wording like:

```text
Требования маркетплейсов нужно сверить с официальными источниками.
PlaceFit не подтверждает юридическое или операционное соответствие.
```

Do not use wording that implies official approval, legal certainty, or automatic
marketplace acceptance.

## Illustrative Rules Are Not Product Logic

Any example table of area, floor, entrance, storage, signage, video surveillance,
or courier access requirements is illustrative until source-tracked and manually
verified.

Values must not be hardcoded as truth until they have:

- marketplace;
- rule text;
- official or approved `source_url`;
- `retrieved_at` or `valid_from`;
- optional `valid_to`;
- `needs_manual_check=true`;
- review notes for legal/product uncertainty.

## MVP Service Logic

```python
def check_marketplace(location):
    warning = (
        "Требования маркетплейсов нужно сверить с официальными источниками; "
        "MVP не подтверждает юридическое или операционное соответствие."
    )
    results = {}
    for marketplace in ["ozon", "wildberries", "yandex_market"]:
        manual_checks = [
            "Проверить зону открытия на официальном сайте маркетплейса",
            "Сверить актуальные требования к площади",
            "Сверить требования к этажу и отдельному входу",
            "Проверить требования к складу, вывеске, видеонаблюдению и юридическим условиям",
        ]
        results[marketplace] = {
            "status": "needs_manual_check",
            "needs_manual_check": True,
            "manual_checks": manual_checks,
            "warning": warning,
        }
    return results
```

## V1.5 Maturity

V1.5 may make marketplace rules more auditable and versioned, but still not an
official compliance engine.

Scope:

- Source-tracked marketplace rule records.
- Rule version history.
- Manual-check status retained.
- Optional internal config/admin interface only if it reduces real maintenance
  pain.
- Comparison of rule versions when sources change.

Acceptance criteria:

- Marketplace rules include source URL and retrieval/validity dates.
- Old analyses remain interpretable.
- UI/report wording still says manual verification is required.
- No official compliance guarantee is implied.
