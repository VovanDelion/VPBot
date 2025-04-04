from .cart import register_cart_handlers
from .user import register_user_handlers
from .menu import register_menu_handlers
from .admin import register_admin_handlers
from .feedback import register_feedback_handlers
from .order import register_order_handlers


def register_all_handlers(dp):
    register_user_handlers(dp)
    register_cart_handlers(dp)
    register_menu_handlers(dp)
    register_admin_handlers(dp)
    register_feedback_handlers(dp)
    register_order_handlers(dp)