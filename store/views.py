from django.shortcuts import render, get_object_or_404, redirect
from store.models import Product, ProductGallery
from category.models import Category
from cart.views import _cart_id
from cart.models import CartItem
from django.db.models import Q
from django.core.paginator import PageNotAnInteger, EmptyPage, Paginator
from store.models import ReviewRating
from store.forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct
from wishlist.models import Wishlist

# Create your views here.
def store(request, category_slug=None):
    category = None
    products = Product.objects.filter(is_available=True).order_by('-id')

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if min_price and max_price:
        min_price = float(min_price)
        max_price = float(max_price)
        products = products.filter(price__range=(min_price, max_price))

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    paginator = Paginator(products, 9)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    products_count = products.count()

    context = {
        'products': paged_products,
        'products_count': products_count,
    }

    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e

    if request.user.is_authenticated:
        wishtlist_product_exists = Wishlist.objects.filter(user=request.user, product=single_product).exists()
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None
        wishtlist_product_exists = None

    # Get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    # Get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context = {
        'single_product': single_product,
        'in_cart'       : in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
        'wishtlist_product_exists': wishtlist_product_exists,
    }
    return render(request, 'store/product-detail.html', context)


def search(request):
    context = {}

    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.filter(
                Q(description__icontains=keyword) | Q(product_name__icontains=keyword)
            ).order_by('-created_date')

            products_count = products.count()

            context = {
                'products': products,
                'keyword': keyword,
                'products_count': products_count,
            }

    return render(request, 'store/store.html', context)


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)
