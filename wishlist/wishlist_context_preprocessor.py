from wishlist.models import Wishlist

def count(request):
    wishlist_count = 0
    
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user)
        wishlist_count = len(wishlist_items)  # Get the count of wishlist items for the authenticated user
    else:
        wishlist_count = 0  # Set wishlist count to 0 if user is not authenticated

    return {'wishlist_count': wishlist_count}
