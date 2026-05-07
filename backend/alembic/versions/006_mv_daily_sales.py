"""006_mv_daily_sales

Materialised view for daily analytics. REFRESH is run by a batch job (Phase 5).
A unique index on sale_date is needed to support REFRESH ... CONCURRENTLY.

Revision ID: 006_mv_daily_sales
Revises: 005_indexes
Create Date: 2026-05-05

"""
from typing import Sequence, Union

from alembic import op


revision: str = "006_mv_daily_sales"
down_revision: Union[str, None] = "005_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE MATERIALIZED VIEW mv_daily_sales AS
        SELECT
            date_trunc('day', o.created_at)::date AS sale_date,
            COUNT(*)                              AS order_count,
            SUM(o.total_amount)                   AS total_revenue,
            COUNT(DISTINCT o.user_id)             AS unique_customers
        FROM orders o
        WHERE o.status <> 'cancelled'
        GROUP BY date_trunc('day', o.created_at)::date
        WITH NO DATA
        """
    )
    op.execute("CREATE UNIQUE INDEX ix_mv_daily_sales_date ON mv_daily_sales(sale_date)")


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_daily_sales")
