from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from cart.models import CartItem
from .forms import OrderForm
import datetime
from .models import Order, Payment, OrderProduct
import json
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.contrib import messages
import datetime
from accounts.models import UserProfile


def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    # Store transaction details inside Payment model
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status'],
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move the cart items to Order Product table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()


        # Reduce the quantity of the sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()

    # Send order recieved email to customer
    mail_subject = 'Thank you for your order!'
    message = render_to_string('orders/order_recieved_email.html', {
        'user': request.user,
        'order': order,
    })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    # Send order number and transaction id back to sendData method via JsonResponse
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)

def place_order(request, total=0, quantity=0,):
    current_user = request.user

    # If the cart count is less than or equal to 0, then redirect back to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total)/100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store all the billing information inside Order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d") #20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payments.html', context)
    else:
        return redirect('checkout')


@require_POST
def place_order_cod(request):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)

    if cart_items.exists():
        # Calculate total and tax
        total = sum(item.product.price * item.quantity for item in cart_items)
        tax = (2 * total) / 100
        order_total = total + tax

        # Fetch user's address information from UserProfile
        try:
            user_profile = current_user.userprofile
            address_line_1 = user_profile.address_line_1
            address_line_2 = user_profile.address_line_2
            city = user_profile.city
            state = user_profile.state
            country = user_profile.country
        except UserProfile.DoesNotExist:
            # If UserProfile does not exist, set address fields to empty strings
            address_line_1 = ''
            address_line_2 = ''
            city = ''
            state = ''
            country = ''

        # Create the Order instance
        order = Order.objects.create(
            user=current_user,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            phone=current_user.phone_number,
            email=current_user.email,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            country=country,
            state=state,
            city=city,
            order_total=order_total,
            tax=tax,
            ip=request.META.get('REMOTE_ADDR'),
            is_ordered=True
        )
        yr = int(datetime.date.today().strftime('%Y'))
        dt = int(datetime.date.today().strftime('%d'))
        mt = int(datetime.date.today().strftime('%m'))
        d = datetime.date(yr,mt,dt)
        current_date = d.strftime("%Y%m%d") #20210305
        order.order_number = current_date + str(order.id)
        order.save()

        # Create Payment instance (for COD, payment_id and method can be 'COD')
        payment = Payment.objects.create(
            user=current_user,
            payment_id='COD',  # Example: 'COD'
            payment_method='Cash on Delivery',  # Example: 'Cash on Delivery'
            amount_paid=order_total,
            status='Pending'  # Example: 'Pending'
        )

        order.payment = payment
        order.save()

        # Create OrderProduct entries for each cart item
        for cart_item in cart_items:
            order_product = OrderProduct.objects.create(
                order=order,
                payment=payment,
                user=current_user,
                product=cart_item.product,
                quantity=cart_item.quantity,
                product_price=cart_item.product.price,
                ordered=True
            )

            # Set variations for the OrderProduct
            variations = cart_item.variations.all()
            order_product.variations.set(variations)

            # Reduce the product stock
            product = cart_item.product
            product.stock -= cart_item.quantity
            product.save()

        # Clear the cart
        cart_items.delete()

        # Send confirmation email to user
        mail_subject = 'Thank you for your order!'
        message = render_to_string('orders/order_recieved_email.html', {'order': order})
        to_email = current_user.email
        email = EmailMessage(mail_subject, message, to=[to_email])
        email.send()

        # Display order confirmation message
        messages.success(request, 'Your order has been placed successfully!')

        # Return JsonResponse with order details
        data = {
            'order_number': order.order_number,
            'order_total': order_total,
            'payment_method': 'Cash on Delivery'  # Example: 'Cash on Delivery'
        }
        return redirect('order_detail', order_id=order.order_number)

    else:
        # Redirect if cart is empty
        return redirect('store')