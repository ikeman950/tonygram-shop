from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .forms import OrderCreateForm
from .models import Order, OrderItem
from .models import Product, Category
from .cart import Cart
from django.db.models import Q


def home(request):
    # Get query parameters
    search_query = request.GET.get('q', '').strip()      # search term
    category_slug = request.GET.get('category')          # category filter

    # Start with all available products
    products = Product.objects.filter(available=True).order_by('-created')

    # Apply category filter if provided
    selected_category = None
    if category_slug:
        try:
            selected_category = Category.objects.get(slug=category_slug)
            products = products.filter(category=selected_category)
        except Category.DoesNotExist:
            pass

    # Apply search filter if query exists
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Get all categories for menu
    categories = Category.objects.all()

    context = {
        'products': products,
        'categories': categories,
        'selected_category': selected_category.slug if selected_category else None,
        'search_query': search_query,  # to keep the search term in input
        'title': 'Welcome to TonyGram Trading',
    }
    return render(request, 'core/home.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    context = {
        'product': product,
        'title': product.name,
    }
    return render(request, 'core/product_detail.html', context)

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, available=True)
    
    quantity = int(request.POST.get('quantity', 1))
    override = request.POST.get('override_quantity') == 'true'  # for cart page updates
    
    cart.add(product=product, quantity=quantity, override_quantity=override)
    
    return redirect('cart_detail')

def cart_detail(request):
    cart = Cart(request)
    context = {
        'cart': cart,
        'title': 'Your Shopping Cart',
    }
    return render(request, 'core/cart_detail.html', context)


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart_detail')


def checkout(request):
    cart = Cart(request)
    
    if len(cart) == 0:
        return redirect('cart_detail')
    
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            
            # Save order items
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )
            
            # Clear cart
            cart.clear()
            
            # Send emails
            # 1. To customer
            customer_subject = f'Order Confirmation - TonyGram Trading #{order.id}'
            customer_message = render_to_string(
                'core/order_confirmation_email.txt',
                {'order': order}
            )
            send_mail(
                customer_subject,
                customer_message,
                settings.DEFAULT_FROM_EMAIL,
                [order.email],   
                fail_silently=False,
            )
            
            # 2. To admin/shop owner
            admin_subject = f'New Order Received - #{order.id}'
            admin_message = render_to_string(
                'core/new_order_alert_email.txt',
                {'order': order}
            )
            send_mail(
                admin_subject,
                admin_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_HOST_USER],  # your email
                fail_silently=False,
            )
            
            request.session['order_id'] = order.id
            return redirect('checkout_success')
    else:
        form = OrderCreateForm()
    
    context = {
        'cart': cart,
        'form': form,
        'title': 'Checkout - TonyGram Trading',
    }
    return render(request, 'core/checkout.html', context)


def checkout_success(request):
    order_id = request.session.get('order_id')
    order = None
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            del request.session['order_id']  # clean up
        except Order.DoesNotExist:
            pass
    
    context = {
        'order': order,
        'title': 'Order Placed Successfully!',
    }
    return render(request, 'core/checkout_success.html', context)

