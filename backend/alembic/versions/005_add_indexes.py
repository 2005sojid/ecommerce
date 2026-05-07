"""005_add_indexes

Revision ID: 005_indexes
Revises: 004_reviews_flash
Create Date: 2026-05-05

"""
from typing import Sequence, Union

from alembic import op


revision: str = "005_indexes"
down_revision: Union[str, None] = "004_reviews_flash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index("ix_products_active_price", "products", ["is_active", "price"])
    op.create_index("ix_orders_user_created", "orders", ["user_id", "created_at"])
    op.create_index("ix_order_events_order_ts", "order_events", ["order_id", "timestamp"])
    op.create_index("ix_reviews_product_id", "reviews", ["product_id"])
    op.create_index("ix_inventory_product_id", "inventory", ["product_id"], unique=True)
    op.execute(
        "CREATE INDEX ix_flash_sales_active ON flash_sales(start_at, end_at) WHERE is_active = true"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_flash_sales_active")
    op.drop_index("ix_inventory_product_id", table_name="inventory")
    op.drop_index("ix_reviews_product_id", table_name="reviews")
    op.drop_index("ix_order_events_order_ts", table_name="order_events")
    op.drop_index("ix_orders_user_created", table_name="orders")
    op.drop_index("ix_products_active_price", table_name="products")
    op.drop_index("ix_products_category_id", table_name="products")
