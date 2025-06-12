from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Order, OrderItem
from .forms import AddToCartForm, CheckoutForm
from django.shortcuts import render
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import requests

# Helper: get cart from session
def get_cart(request):
    return request.session.get('cart', {})

def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = AddToCartForm()
    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            cart = get_cart(request)
            cart[str(product.id)] = cart.get(str(product.id), 0) + form.cleaned_data['quantity']
            request.session['cart'] = cart
            return redirect('cart')
    return render(request, 'product_detail.html', {'product': product, 'form': form})

def cart_view(request):
    cart = get_cart(request)
    items = []
    total = 0
    for pk, qty in cart.items():
        product = get_object_or_404(Product, pk=pk)
        subtotal = product.price * qty
        items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})
        total += subtotal
    return render(request, 'cart.html', {'items': items, 'total': total})


def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('product_list')  # fallback if cart is empty

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Store form data in session to use later after payment
            request.session['checkout_info'] = {
                'name': form.cleaned_data['name'],
                'email': form.cleaned_data['email'],
                'phone': form.cleaned_data['phone'],
                'address': form.cleaned_data['address'],
            }
            return redirect('initiate_payment')
    else:
        form = CheckoutForm()

    # Calculate total for display
    total = 0
    items = []
    for pk, quantity in cart.items():
        product = Product.objects.get(pk=pk)
        subtotal = product.price * quantity
        total += subtotal
        items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})

    context = {
        'form': form,
        'items': items,
        'total': total,
    }

    return render(request, 'checkout.html', context)


def update_cart(request, product_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        cart = request.session.get('cart', {})

        product_id_str = str(product_id)
        if product_id_str in cart:
            if action == 'decrease':
                if cart[product_id_str] > 1:
                    cart[product_id_str] -= 1
                else:
                    del cart[product_id_str]
            elif action == 'remove':
                del cart[product_id_str]

        request.session['cart'] = cart

    return redirect('cart')  # Assuming 'cart' is the name of your cart page URL

# views.py


def initiate_payment(request):
    checkout_info = request.session.get('checkout_info')
    cart = request.session.get('cart', {})

    if not checkout_info or not cart:
        return redirect('checkout')

    # Recalculate amount from cart
    total = 0
    for pk, quantity in cart.items():
        product = Product.objects.get(pk=pk)
        subtotal = product.price * quantity
        total += subtotal

    context = {
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
        'email': checkout_info.get('email'),
        'amount': total,  # 💡 In Naira, NOT multiplied yet
        'total': total,
    }

    return render(request, 'payment.html', context)


def verify_payment(request, reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
    }
    response = requests.get(url, headers=headers)
    data = response.json()

    if data['status'] and data['data']['status'] == 'success':
        cart = request.session.get('cart', {})
        checkout_info = request.session.get('checkout_info', {})

        if not cart or not checkout_info:
            return redirect('cart')  # fallback

        # ✅ Create the order after successful payment
        order = Order.objects.create(
            customer_name=checkout_info['name'],
            customer_email=checkout_info['email'],
            phone=checkout_info['phone'],
            address=checkout_info['address'],
            paid=True,
            reference=reference
        )

        for pk, qty in cart.items():
            product = get_object_or_404(Product, pk=pk)
            OrderItem.objects.create(order=order, product=product, quantity=qty)

        # ✅ Clear session
        request.session['cart'] = {}
        request.session['checkout_info'] = {}

        return render(request, 'payment_success.html', {'order': order})

    return render(request, 'payment_failed.html')
