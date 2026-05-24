"""Manual-check-only marketplace requirements for MVP."""

from app.schemas.report import (
    MarketplaceRequirementResult,
    MarketplaceRequirements,
)

_WARNING = "Требования маркетплейсов нужно сверить с официальными источниками."


def get_marketplace_requirements() -> MarketplaceRequirements:
    """Return safe MVP marketplace checks without automatic pass/fail."""

    return MarketplaceRequirements(
        ozon=MarketplaceRequirementResult(
            status="needs_manual_check",
            needs_manual_check=True,
            manual_checks=[
                "Проверить актуальную зону открытия ПВЗ на официальных ресурсах Ozon.",
                "Сверить требования к помещению и договору перед подписанием аренды.",
            ],
            warning=_WARNING,
        ),
        wildberries=MarketplaceRequirementResult(
            status="needs_manual_check",
            needs_manual_check=True,
            manual_checks=[
                "Проверить актуальные условия открытия ПВЗ у Wildberries.",
                "Сверить требования к площади, входу, складу и режиму работы вручную.",
            ],
            warning=_WARNING,
        ),
        yandex_market=MarketplaceRequirementResult(
            status="needs_manual_check",
            needs_manual_check=True,
            manual_checks=[
                "Уточнить доступность формата ПВЗ и зоны открытия у Яндекс Маркета.",
                "Проверить требования к помещению по официальным источникам.",
            ],
            warning=_WARNING,
        ),
    )
