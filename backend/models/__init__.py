# models/__init__.py
from .user import User, Address,EmailChangeRequestModel
from .category import Category
from .orders import Order, OrderItem
from .payments import Payment
from .products import Product,ProductVariant,ProductVariantAttribute,ProductVariantImage
from .promocode import PromoCode
from .tag import Tag
from .currency import Currency
# import other models too...

from core.database import Base,engine_db  # or wherever your Base is defined


__all__ = ['User', 'Address','EmailChangeRequestModel',"Category", "Currency", 'Order','OrderItem','Payment','Product','ProductVariant','ProductVariantAttribute','ProductVariantImage','PromoCode','Tag']
