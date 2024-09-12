
from decimal import Decimal
import uuid
from django.db import models
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from User.models import Address, OrderAddress


class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(max_length=255, blank=True)
    cat_image = models.ImageField(upload_to='photos/categories', blank=True)
    is_active = models.BooleanField(default=True)
    category_offer = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, )

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.category_name
    
class SubCategory(models.Model):
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
    subcategory_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'SubCategory'
        verbose_name_plural = 'SubCategories'
        unique_together = ('category', 'subcategory_name')  # Ensure unique subcategory names within each category

    def __str__(self):
        return f"{self.subcategory_name} ({self.category.category_name})"
    

class Brand(models.Model):
    brand_name = models.CharField(max_length=255)   
    category = models.ManyToManyField(Category, related_name='brands')
    is_active = models.BooleanField(default=True)
    brand_offer = models.DecimalField(max_digits=5, decimal_places=2, default=0.00,)

    def __str__(self):
        return self.brand_name
    
class Size(models.Model):
    size_name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.size_name
    
class Color(models.Model):
    color_name = models.CharField(max_length=50, unique=True)
    color_code = models.CharField(max_length=10)  # Assuming you store color code as a string

    def __str__(self):
        return self.color_name
    

class Product(models.Model):
    AVAILABILITY_CHOICES = [
        ('in_stock', _('In Stock')),
        ('out_of_stock', _('Out of Stock')),
    ]

    title = models.CharField(max_length=100)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.ForeignKey(Brand, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    max_qty_per_person = models.PositiveIntegerField(default=2)
    in_stock = models.BooleanField(default=True)
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='in_stock')
    trending = models.BooleanField(default=False, help_text=_('0=default, 1=Hidden'))
    rating = models.PositiveIntegerField(default=0, help_text=_('Rating from 1 to 5'), validators=[
        MinValueValidator(1),
        MaxValueValidator(5)
    ])
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='product_creator', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    product_image = models.ImageField(upload_to='photos/products', verbose_name=_("Product Image"), default='default_product_image.jpg')
    featured = models.BooleanField(default=False, help_text=_('Is this product featured?'))
    popularity = models.IntegerField(default=0)
    sizes = models.ManyToManyField(Size, blank=True)
    colors = models.ManyToManyField(Color, blank=True)
    product_offer = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text=_('Discount percentage applied to the product'))
    
    

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
    @property
    def offer_price(self):
        category_offer = self.category.category_offer if self.category else 0
        brand_offer = self.brand.brand_offer if self.brand else 0
        final_discount = max(self.product_offer, brand_offer,category_offer)
        discounted_price = self.original_price * (1 - (final_discount / 100))
        return max(discounted_price, 0)
    
    def get_best_offer(self):
        
        category_offer = self.category.category_offer if self.category else 0
        brand_offer = self.brand.brand_offer if self.brand else 0
        offers = {
            'product_offer': self.product_offer,
            'category_offer': category_offer,
            'brand_offer': brand_offer
        }
        best_offer_type = max(offers, key=offers.get)
        best_offer_percentage = offers[best_offer_type]
        return best_offer_percentage

    @property
    def main_image(self):
        return self.product_image.url if self.product_image else None
    
    def save(self, *args, **kwargs):
        if self.quantity == 0:
            self.availability_status = 'out_of_stock'
        elif self.quantity == 1:
            self.availability_status = 'in_stock'
        if self.original_price < 0:
            raise ValidationError("Original price cannot be negative.")
        if self.product_offer < 0 or self.product_offer > 100:
            raise ValidationError("Product offer must be between 0 and 100 percent.")
        super(Product, self).save(*args, **kwargs)



class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='photos/products')
    is_main = models.BooleanField(default=False)

    def __str__(self):
        return f"Image of {self.product.title}"
    

class Coupon(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
    ]

    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateField()
    valid_to = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='inactive')

    def __str__(self):
        return self.code

    def update_status(self):
        today = timezone.now().date()
        if self.valid_from <= today <= self.valid_to:
            self.status = 'active'
        elif today < self.valid_from:
            self.status = 'inactive'
        else:
            self.status = 'expired'
    

class Order(models.Model):
    STATUS_CHOICES = (
        ('Ordered', 'Ordered'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Returned', 'Returned'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.ForeignKey(OrderAddress, on_delete=models.CASCADE, related_name='orders')
    payment_method = models.CharField(max_length=50,null=False,default=False)
    order_notes = models.TextField(blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4().hex)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Ordered') 
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending') 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_id = models.CharField(max_length=255, blank=True, null=True) 
    wallet_credit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)  
   

    def save(self, *args, **kwargs):
        if not self.order_number:
            last_order = Order.objects.order_by('-id').first()
            new_number = last_order.order_number + 1 if last_order else 1
            self.order_number = str(new_number)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Order {self.id} - {self.user.username}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.product.title} - {self.quantity}'
    

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)

    @property
    def total_price(self):
        total_price = sum(item.total_price for item in self.cartitem_set.all())
        if self.coupon:
            discount = self.coupon.discount
            discount_amount = (total_price * discount) / Decimal('100.00')
            total_price -= discount_amount
        return total_price

    
    


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    size = models.ForeignKey(Size, on_delete=models.CASCADE, null=True, blank=True)
    color = models.ForeignKey(Color, on_delete=models.CASCADE, null=True, blank=True)
    

    @property
    def offer_price(self):
        return self.product.offer_price

    @property
    def total_price(self):
        return self.offer_price * self.quantity
    



        self.save(update_fields=['status'])

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)  # Stock quantity for this variant
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price for this variant, if different

    class Meta:
        unique_together = ('product', 'size', 'color')

    def __str__(self):
        return f'{self.product.title} - {self.size.size_name} - {self.color.color_name}'