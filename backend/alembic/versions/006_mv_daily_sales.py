from typing import Sequence, Union
from alembic import op
revision: str = '006_mv_daily_sales'
down_revision: Union[str, None] = '005_indexes'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("\n        CREATE MATERIALIZED VIEW mv_daily_sales AS\n        SELECT\n            date_trunc('day', o.created_at)::date AS sale_date,\n            COUNT(*)                              AS order_count,\n            SUM(o.total_amount)                   AS total_revenue,\n            COUNT(DISTINCT o.user_id)             AS unique_customers\n        FROM orders o\n        WHERE o.status <> 'cancelled'\n        GROUP BY date_trunc('day', o.created_at)::date\n        WITH NO DATA\n        ")
    op.execute('CREATE UNIQUE INDEX ix_mv_daily_sales_date ON mv_daily_sales(sale_date)')

def downgrade() -> None:
    op.execute('DROP MATERIALIZED VIEW IF EXISTS mv_daily_sales')
