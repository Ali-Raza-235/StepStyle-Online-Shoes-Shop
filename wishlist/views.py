from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Wishlist
from store.models import Product
from django.contrib.auth.decorators import login_required

# Create your views here.

def wishlist(request):
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user)
    else:
        messages.warning(request, 'You must be logged in to view the wishlist.')
        return redirect('login')

    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'store/wishlist.html', context)


@login_required(login_url='login')
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    
    # Check if the product is already in the user's wishlist
    if Wishlist.objects.filter(user=request.user, product=product).exists():
        messages.warning(request, 'This product is already in your wishlist.')
    else:
        # Add the product to the user's wishlist
        Wishlist.objects.create(user=request.user, product=product)
        messages.success(request, 'Product added to your wishlist.')

    return redirect('wishlist')

def remove_from_wishlist(request, wishlist_item_id):
    if request.method == 'POST':
        wishlist_item = get_object_or_404(Wishlist, pk=wishlist_item_id)
        wishlist_item.delete()
        messages.success(request, 'Product removed from wishlist successfully.')
        return redirect('wishlist')
    else:
        messages.error(request, 'Invalid request method.')
        return redirect('wishlist')
