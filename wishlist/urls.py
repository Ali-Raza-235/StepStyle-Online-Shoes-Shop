from django.urls import path
from wishlist import views

urlpatterns = [
    path('', views.wishlist, name='wishlist'),
    path('remove/<int:wishlist_item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
]