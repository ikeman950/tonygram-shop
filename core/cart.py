from decimal import Decimal, InvalidOperation
from django.conf import settings
from .models import Product


class Cart:
    """
    Session-based shopping cart.
    Prices are stored as strings to avoid JSON serialization issues with Decimal.
    """

    def __init__(self, request):
        """
        Initialize the cart from the current session.
        If no cart exists, create an empty one.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = {}
        self.cart = cart
        
        

    def __iter__(self):
        """
        Iterate over cart items without modifying stored session data.
        Returns enhanced item dictionaries with product objects and calculated totals.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids, available=True)

        # Work on a copy to prevent any mutation of session data
        cart_copy = self.cart.copy()

        # Attach product objects
        for product in products:
            pid_str = str(product.id)
            if pid_str in cart_copy:
                cart_copy[pid_str]['product'] = product

        # Yield safe, computed item dictionaries
        for item in cart_copy.values():
            try:
                price = Decimal(item['price'])
            except (InvalidOperation, TypeError, KeyError):
                price = Decimal('0.00')

            total_price = price * item.get('quantity', 0)

            yield {
                'product': item.get('product'),
                'price': price,
                'quantity': item.get('quantity', 0),
                'total_price': total_price,
            }

    def __len__(self):
        """
        Return total number of items in the cart (sum of quantities).
        """
        return sum(item.get('quantity', 0) for item in self.cart.values())

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity.
        """
        product_id = str(product.id)

        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price),  # Store as string for JSON safety
            }

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self.save()

    def save(self):
        """
        Mark session as modified and save cart data.
        """
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

        
    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        """
        Remove the entire cart from the session.
        """
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
            self.session.modified = True

    def get_total_price(self):
        """
        Calculate and return the total price of all items in the cart.
        """
        total = Decimal('0.00')
        for item in self.cart.values():
            try:
                price = Decimal(item['price'])
                total += price * item.get('quantity', 0)
            except (InvalidOperation, TypeError, KeyError):
                pass  # Skip invalid items silently
        return total