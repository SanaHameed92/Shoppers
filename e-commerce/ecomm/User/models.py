from django.db import models
from django.conf import settings
from django.utils import timezone
from django.apps import apps


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20)
    street_address = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    email = models.EmailField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def get_full_address(self):
        return (f"{self.first_name} {self.last_name}, {self.street_address}, {self.city}, "
                f"{self.state}, {self.country}, {self.postal_code}")

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.state}, {self.country} - {self.postal_code}"
    

class OrderAddress(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20)
    street_address = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)
    email = models.EmailField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def get_full_address(self):
        return (f"{self.first_name} {self.last_name}, {self.street_address}, {self.city}, "
                f"{self.state}, {self.country}, {self.postal_code}")

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.state}, {self.country} - {self.postal_code}"
    
class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, null=True, default=None)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"Wishlist item for {self.user} - Product ID: {self.product_id}"

    @property
    def product_instance(self):
        Product = apps.get_model('products', 'Product')
        return Product.objects.get(id=self.product_id)