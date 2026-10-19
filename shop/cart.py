from decimal import Decimal

from .models import Product

CART_SESSION_KEY = 'cart'
MAX_QUANTITY = 99


class Cart:
    """Panier stocké en session : {id_produit: quantité}. Les prix sont toujours relus en base."""

    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.get(CART_SESSION_KEY, {})

    def add(self, product, quantity=1):
        key = str(product.id)
        self.cart[key] = min(self.cart.get(key, 0) + quantity, MAX_QUANTITY)
        self.save()

    def update(self, product, quantity):
        key = str(product.id)
        if quantity <= 0:
            self.cart.pop(key, None)
        else:
            self.cart[key] = min(quantity, MAX_QUANTITY)
        self.save()

    def remove(self, product):
        if self.cart.pop(str(product.id), None) is not None:
            self.save()

    def clear(self):
        self.session.pop(CART_SESSION_KEY, None)
        self.cart = {}

    def save(self):
        self.session[CART_SESSION_KEY] = self.cart
        self.session.modified = True

    def get_items(self):
        products = Product.objects.filter(id__in=self.cart.keys(), available=True)
        items = []
        for product in products:
            quantity = self.cart[str(product.id)]
            items.append({
                'product': product,
                'quantity': quantity,
                'total_price': product.price * quantity,
            })

        # Retire les articles supprimés ou devenus indisponibles
        found = {str(item['product'].id) for item in items}
        if found != set(self.cart.keys()):
            self.cart = {key: qty for key, qty in self.cart.items() if key in found}
            self.save()
        return items

    @staticmethod
    def get_total(items):
        return sum((item['total_price'] for item in items), Decimal('0'))

    def __len__(self):
        return sum(self.cart.values())
