"""Deterministic fallback report provider."""

from app.config.prompts.v1_0 import PROMPT_VERSION
from app.schemas.report import ReportResult
from app.services.report import PreparedAnalysisReportInput


class FallbackReportProvider:
    """Build a deterministic Russian report without calling an LLM."""

    def generate(self, report_input: PreparedAnalysisReportInput) -> ReportResult:
        """Return a human-readable fallback report."""

        score = report_input.score
        details = score.details
        finance = report_input.finance
        competitors = report_input.competitors
        nearest = (
            f"{competitors.nearest_competitor_distance_m} м"
            if competitors.nearest_competitor_distance_m is not None
            else "не найден"
        )
        expected_income = (
            str(finance.expected_gross_income_by_user)
            if finance.expected_gross_income_by_user is not None
            else "не указан"
        )
        net_profit = (
            str(finance.net_profit)
            if finance.net_profit is not None
            else "не рассчитана"
        )
        payback = (
            f"{finance.payback_months}"
            if finance.payback_months is not None
            else "не рассчитана"
        )
        checklist = "\n".join(f"- {item}" for item in report_input.checklist)

        text = (
            "## Краткий вывод\n"
            f"Адрес: {report_input.location.normalized_address}. "
            f"Итоговое решение: {score.decision}. "
            "Вывод основан только на детерминированных расчётах PlaceFit.\n\n"
            "## Итоговая оценка\n"
            f"- Score: {score.total_score}/100\n"
            f"- Confidence: {score.confidence_score}/100\n"
            f"- Решение: {score.decision}\n\n"
            "## Разбивка score\n"
            f"- Спрос: {details.demand_score}/35\n"
            f"- Конкуренция: {details.competition_score}/25\n"
            f"- Аренда: {details.rent_score}/20\n"
            f"- Помещение: {details.premises_score}/10\n"
            f"- Доступность: {details.accessibility_score}/10\n\n"
            "## Конкуренция\n"
            f"- 300 м: {competitors.competitors_300m}\n"
            f"- 500 м: {competitors.competitors_500m}\n"
            f"- 700 м: {competitors.competitors_700m}\n"
            f"- Ближайший конкурент: {nearest}\n\n"
            "## Финансовая модель\n"
            f"- Ежемесячные расходы: {finance.monthly_costs} ₽\n"
            f"- Необходимый валовый доход: {finance.required_gross_income} ₽\n"
            f"- Ожидаемый валовый доход пользователя: {expected_income} ₽\n"
            f"- Чистая прибыль: {net_profit} ₽\n"
            f"- Окупаемость: {payback} мес.\n\n"
            "Ожидаемый доход — гипотеза пользователя, а не прогноз системы "
            "и не гарантия результата.\n\n"
            "## Требования маркетплейсов\n"
            "Статусы маркетплейсов в MVP означают только необходимость "
            "ручной проверки. Перед решением нужно сверить актуальные "
            "условия по официальным источникам.\n\n"
            "## Что проверить дальше\n"
            f"{checklist}\n"
        )
        return ReportResult(
            status="fallback",
            text=text,
            provider="fallback",
            model="none",
            prompt_version=PROMPT_VERSION,
        )
