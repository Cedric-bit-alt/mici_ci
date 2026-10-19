from django.conf import settings

from .cart import Cart


def cart(request):
    return {
        'cart_count': len(Cart(request)),
        'shop_currency': settings.SHOP_CURRENCY,
    }
