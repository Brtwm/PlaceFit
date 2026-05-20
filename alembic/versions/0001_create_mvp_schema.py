"""Create MVP schema and seed scoring rules.

Revision ID: 0001_create_mvp_schema
Revises:
Create Date: 2026-05-19
"""

import json
from typing import Any

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

revision = "0001_create_mvp_schema"
down_revision = None
branch_labels = None
depends_on = None


SCORING_RULES_V1: dict[str, Any] = {
    "scoring_version": "v1.0",
    "component_max_scores": {
        "demand": 35,
        "competition": 25,
        "rent": 20,
        "premises": 10,
        "accessibility": 10,
    },
    "demand": {
        "base": 5,
        "high_density_area": 15,
        "new_residential_area": 15,
    },
    "competition": {
        "radius_300m_zero": 10,
        "radius_300m_one": 7,
        "radius_300m_two": 4,
        "radius_300m_three_or_more": 1,
        "radius_700m_zero_to_two": 10,
        "radius_700m_three_to_four": 7,
        "radius_700m_five_to_six": 4,
        "radius_700m_seven_or_more": 1,
        "nearest_over_500m": 5,
        "nearest_300m_to_500m": 3,
        "nearest_150m_to_300m": 1,
        "nearest_under_150m": 0,
        "no_known_competitor": 5,
        "unknown_nearest_with_competitors": 0,
        "count_one": 1,
        "count_two": 2,
        "count_three": 3,
        "count_five": 5,
        "count_seven": 7,
        "distance_150m": 150,
        "distance_300m": 300,
        "distance_500m": 500,
    },
    "rent": {
        "cheap_max": 60000,
        "normal_max": 90000,
        "high_max": 130000,
        "cheap_score": 20,
        "normal_score": 15,
        "high_score": 8,
        "expensive_score": 2,
    },
    "premises": {
        "first_floor": 3,
        "separate_entrance": 2,
        "ideal_area": 2,
        "acceptable_area": 1,
        "bad_area": 0,
        "storage_area": 2,
        "signage_possible": 1,
        "acceptable_area_min_exclusive": 15.0,
        "ideal_area_min": 20.0,
        "ideal_area_max": 60.0,
        "acceptable_area_max": 80.0,
    },
    "accessibility": {
        "parking": 3,
        "bus_stop_nearby": 3,
        "good_visibility": 2,
        "separate_entrance": 2,
    },
    "confidence": {
        "source_completeness_two_or_more": 25,
        "source_completeness_one": 15,
        "source_completeness_none": 0,
        "freshness_under_7_days": 20,
        "freshness_under_30_days": 15,
        "freshness_old_or_unknown": 5,
        "freshness_days_7": 7,
        "freshness_days_30": 30,
        "manual_input_verified": 20,
        "manual_input_manual": 10,
        "manual_input_partial": 5,
        "competitor_count_three_or_more": 20,
        "competitor_count_one_to_two": 10,
        "competitor_count_none": 5,
        "finance_with_expected_income": 15,
        "finance_without_expected_income": 5,
        "source_count_one": 1,
        "source_count_two": 2,
        "competitor_count_one": 1,
        "competitor_count_three": 3,
    },
    "finance_defaults": {
        "salary": 120000,
        "taxes": 30000,
        "utilities": 10000,
        "internet": 5000,
        "consumables": 10000,
        "other_costs": 15000,
        "reserve": 20000,
        "desired_profit": 80000,
        "investment": 600000,
        "payback_round_digits": 1,
    },
    "decision": {
        "high_score_threshold": 75,
        "mid_score_threshold": 60,
        "high_rent_threshold": 130000,
        "consider": "можно рассматривать",
        "check_more": "проверить дополнительно",
        "likely_no": "скорее не открывать",
        "high_rent_warning": (
            "Высокая аренда: проверьте устойчивость экономики ПВЗ."
        ),
        "unprofitable_warning": "При указанном доходе точка убыточна.",
        "income_missing_warning": (
            "Доход не указан: финальная окупаемость не рассчитана."
        ),
    },
}


def _timestamp_col(name: str) -> sa.Column[Any]:
    return sa.Column(
        name,
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
    )


def upgrade() -> None:
    """Create MVP tables and seed active scoring version."""

    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("normalized_address", sa.Text(), nullable=True),
        sa.Column("city", sa.Text(), server_default=sa.text("'Краснодар'")),
        sa.Column("region", sa.Text(), nullable=True),
        sa.Column("lat", sa.Double(), nullable=True),
        sa.Column("lon", sa.Double(), nullable=True),
        sa.Column(
            "geom",
            Geography("POINT", srid=4326, spatial_index=False),
            nullable=True,
        ),
        sa.Column(
            "business_type",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'pvz'"),
        ),
        sa.Column("rent", sa.Integer(), nullable=True),
        sa.Column("area_m2", sa.Numeric(), nullable=True),
        sa.Column("floor", sa.Integer(), nullable=True),
        sa.Column("first_floor", sa.Boolean(), nullable=True),
        sa.Column("separate_entrance", sa.Boolean(), nullable=True),
        sa.Column("parking", sa.Boolean(), nullable=True),
        sa.Column("signage_possible", sa.Boolean(), nullable=True),
        sa.Column("storage_area", sa.Boolean(), nullable=True),
        sa.Column("repair_condition", sa.Text(), nullable=True),
        sa.Column("new_residential_area", sa.Boolean(), nullable=True),
        sa.Column("high_density_area", sa.Boolean(), nullable=True),
        sa.Column("bus_stop_nearby", sa.Boolean(), nullable=True),
        sa.Column("good_visibility", sa.Boolean(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("geocoding_source", sa.Text(), nullable=True),
        sa.Column("geocoding_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("geocoding_confidence", sa.Numeric(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        _timestamp_col("created_at"),
        _timestamp_col("updated_at"),
    )
    op.create_index(
        "idx_locations_geom",
        "locations",
        ["geom"],
        postgresql_using="gist",
    )
    op.create_index("idx_locations_city", "locations", ["city"])
    op.create_index("idx_locations_business_type", "locations", ["business_type"])

    op.create_table(
        "pois",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("brand", sa.Text(), nullable=True),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("lat", sa.Double(), nullable=True),
        sa.Column("lon", sa.Double(), nullable=True),
        sa.Column(
            "geom",
            Geography("POINT", srid=4326, spatial_index=False),
            nullable=True,
        ),
        sa.Column("rating", sa.Numeric(), nullable=True),
        sa.Column("reviews_count", sa.Integer(), nullable=True),
        _timestamp_col("fetched_at"),
        _timestamp_col("created_at"),
        _timestamp_col("updated_at"),
        sa.UniqueConstraint("source", "external_id", name="uq_pois_source_external_id"),
    )
    op.create_index("idx_pois_geom", "pois", ["geom"], postgresql_using="gist")
    op.create_index("idx_pois_brand", "pois", ["brand"])

    op.create_table(
        "scoring_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_type", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("rules", postgresql.JSONB(), nullable=False),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        _timestamp_col("created_at"),
        sa.UniqueConstraint(
            "business_type",
            "version",
            name="uq_scoring_versions_business_type_version",
        ),
    )
    op.create_index(
        "idx_scoring_versions_business_type",
        "scoring_versions",
        ["business_type"],
    )
    op.create_index(
        "ux_scoring_versions_one_active_per_business_type",
        "scoring_versions",
        ["business_type"],
        unique=True,
        postgresql_where=sa.text("active"),
    )

    rules_json = json.dumps(SCORING_RULES_V1, ensure_ascii=False).replace("'", "''")
    op.execute(
        f"""
        INSERT INTO scoring_versions (business_type, version, rules, active)
        VALUES ('pvz', 'v1.0', '{rules_json}'::jsonb, true)
        """
    )

    op.create_table(
        "location_poi_distances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "location_id",
            sa.Integer(),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "poi_id",
            sa.Integer(),
            sa.ForeignKey("pois.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("distance_m", sa.Integer(), nullable=False),
        sa.Column("radius_bucket", sa.Text(), nullable=True),
        _timestamp_col("created_at"),
        sa.UniqueConstraint(
            "location_id",
            "poi_id",
            name="uq_location_poi_distances_location_poi",
        ),
    )
    op.create_index(
        "idx_location_poi_distances_location_id",
        "location_poi_distances",
        ["location_id"],
    )
    op.create_index(
        "idx_location_poi_distances_poi_id",
        "location_poi_distances",
        ["poi_id"],
    )

    op.create_table(
        "scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "location_id",
            sa.Integer(),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "scoring_version_id",
            sa.Integer(),
            sa.ForeignKey("scoring_versions.id"),
            nullable=False,
        ),
        sa.Column("demand_score", sa.Integer(), nullable=True),
        sa.Column("competition_score", sa.Integer(), nullable=True),
        sa.Column("rent_score", sa.Integer(), nullable=True),
        sa.Column("premises_score", sa.Integer(), nullable=True),
        sa.Column("accessibility_score", sa.Integer(), nullable=True),
        sa.Column("total_score", sa.Integer(), nullable=True),
        sa.Column("confidence_score", sa.Integer(), nullable=True),
        sa.Column("decision", sa.Text(), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        _timestamp_col("created_at"),
        sa.CheckConstraint(
            "total_score IS NULL OR total_score BETWEEN 0 AND 100",
            name="ck_scores_total_score_range",
        ),
        sa.CheckConstraint(
            "confidence_score IS NULL OR confidence_score BETWEEN 0 AND 100",
            name="ck_scores_confidence_score_range",
        ),
    )

    op.create_table(
        "financial_models",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "location_id",
            sa.Integer(),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rent", sa.Integer(), nullable=True),
        sa.Column("salary", sa.Integer(), server_default=sa.text("120000")),
        sa.Column("taxes", sa.Integer(), server_default=sa.text("30000")),
        sa.Column("utilities", sa.Integer(), server_default=sa.text("10000")),
        sa.Column("internet", sa.Integer(), server_default=sa.text("5000")),
        sa.Column("consumables", sa.Integer(), server_default=sa.text("10000")),
        sa.Column("other_costs", sa.Integer(), server_default=sa.text("15000")),
        sa.Column("reserve", sa.Integer(), server_default=sa.text("20000")),
        sa.Column("desired_profit", sa.Integer(), server_default=sa.text("80000")),
        sa.Column("investment", sa.Integer(), server_default=sa.text("600000")),
        sa.Column("monthly_costs", sa.Integer(), nullable=True),
        sa.Column("required_gross_income", sa.Integer(), nullable=True),
        sa.Column("expected_gross_income_by_user", sa.Integer(), nullable=True),
        sa.Column("net_profit", sa.Integer(), nullable=True),
        sa.Column("payback_months", sa.Numeric(), nullable=True),
        _timestamp_col("created_at"),
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "location_id",
            sa.Integer(),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("report_text", sa.Text(), nullable=True),
        sa.Column("report_json", postgresql.JSONB(), nullable=True),
        sa.Column("provider", sa.Text(), nullable=True),
        sa.Column("model_name", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.Text(), nullable=True),
        sa.Column("input_json_hash", sa.Text(), nullable=True),
        sa.Column("temperature", sa.Numeric(), nullable=True),
        sa.Column("tokens_input", sa.Integer(), nullable=True),
        sa.Column("tokens_output", sa.Integer(), nullable=True),
        sa.Column("generation_status", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        _timestamp_col("created_at"),
    )

    op.create_table(
        "marketplace_requirements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("marketplace", sa.Text(), nullable=False),
        sa.Column("business_type", sa.Text(), nullable=False),
        sa.Column("requirement_key", sa.Text(), nullable=False),
        sa.Column("requirement_value", postgresql.JSONB(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        _timestamp_col("created_at"),
        sa.UniqueConstraint(
            "marketplace",
            "business_type",
            "requirement_key",
            name="uq_marketplace_requirements_marketplace_business_key",
        ),
    )
    op.create_index(
        "idx_marketplace_requirements_marketplace",
        "marketplace_requirements",
        ["marketplace"],
    )
    op.create_index(
        "idx_marketplace_requirements_business_type",
        "marketplace_requirements",
        ["business_type"],
    )


def downgrade() -> None:
    """Drop MVP tables in reverse dependency order."""

    op.drop_index(
        "idx_marketplace_requirements_business_type",
        table_name="marketplace_requirements",
    )
    op.drop_index(
        "idx_marketplace_requirements_marketplace",
        table_name="marketplace_requirements",
    )
    op.drop_table("marketplace_requirements")
    op.drop_table("reports")
    op.drop_table("financial_models")
    op.drop_table("scores")
    op.drop_index(
        "idx_location_poi_distances_poi_id",
        table_name="location_poi_distances",
    )
    op.drop_index(
        "idx_location_poi_distances_location_id",
        table_name="location_poi_distances",
    )
    op.drop_table("location_poi_distances")
    op.drop_index(
        "ux_scoring_versions_one_active_per_business_type",
        table_name="scoring_versions",
    )
    op.drop_index(
        "idx_scoring_versions_business_type",
        table_name="scoring_versions",
    )
    op.drop_table("scoring_versions")
    op.drop_index("idx_pois_brand", table_name="pois")
    op.drop_index("idx_pois_geom", table_name="pois", postgresql_using="gist")
    op.drop_table("pois")
    op.drop_index("idx_locations_business_type", table_name="locations")
    op.drop_index("idx_locations_city", table_name="locations")
    op.drop_index("idx_locations_geom", table_name="locations", postgresql_using="gist")
    op.drop_table("locations")
