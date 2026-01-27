# core/context_processors.py
from .cart import Cart

def cart(request):
    """
    Adds the cart object to every template context.
    """
    return {
        'cart': Cart(request)
    }