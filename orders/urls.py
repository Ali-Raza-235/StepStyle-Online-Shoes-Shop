from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payments, name='payments'),
    path('place_order_cod/', views.place_order_cod, name='place_order_cod'),
]
