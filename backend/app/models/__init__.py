"""Import all models so that Base.metadata knows about them (needed for Alembic)."""
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem, OrderStatus
from app.models.order_event import OrderEvent
from app.models.review import Review
from app.models.flash_sale import FlashSale

__all__ = [
    "User",
    "UserRole",
    "Category",
    "Product",
    "Inventory",
    "Order",
    "OrderItem",
    "OrderStatus",
    "OrderEvent",
    "Review",
    "FlashSale",
]
