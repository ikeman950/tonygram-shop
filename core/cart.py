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
         product_ids = self.cart.keys()
         products = Product.objects.filter(id__in=product_ids)  # Remove available=True to include even deleted ones temporarily

         cart_copy = self.cart.copy()

        for product in products:
           pid_str = str(product.id)
           if pid_str in cart_copy:
              cart_copy[pid_str]['product'] = product

       for item in cart_copy.values():
          price = Decimal(item['price']) if 'price' in item else Decimal('0.00')
          quantity = item.get('quantity', 0)
          product = item.get('product')  # May be None if deleted

          total_price = price * quantity

          yield {
             'product': product,  # Can be None
             'price': price,
             'quantity': quantity,
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
