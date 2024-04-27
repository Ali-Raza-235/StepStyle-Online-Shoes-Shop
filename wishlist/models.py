from django.db import models
from store.models import Product
from accounts.models import Account

# Create your models here.
class Wishlist(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Wishlist'  
    
    def __str__(self):
        return self.product.product_name