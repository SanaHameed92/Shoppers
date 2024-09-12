from datetime import timezone
from django.contrib import admin

# Register your models here.
from .models import Coupon, Product, Category, Brand, Size, Color, ProductImage,Order,OrderItem,ProductVariant,OrderAddress





admin.site.register(ProductVariant)
admin.site.register(ProductImage)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(OrderAddress)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'brand', 'quantity', 'original_price','product_offer', 'in_stock', 'trending', 'rating', 'created_at', 'updated_at')
    list_filter = ('category', 'brand', 'in_stock', 'trending')
    search_fields = ('title', 'category__category_name', 'brand__brand_name')
    raw_id_fields = ('category', 'brand')
    filter_horizontal = ('sizes', 'colors')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name','category_offer' ,'is_active')
    search_fields = ('category_name',)
    list_filter = ('is_active',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('brand_name','brand_offer', 'is_active')
    search_fields = ('brand_name',)
    list_filter = ('is_active',)
    filter_horizontal = ('category',)

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('size_name',)
    search_fields = ('size_name',)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('color_name', 'color_code')
    search_fields = ('color_name', 'color_code')
    

class CouponAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'discount', 'valid_from', 'valid_to', 'status')
    list_filter = ('status', 'valid_from', 'valid_to')
    search_fields = ('name', 'code')
    ordering = ('-valid_to',)  # Order by expiration date in descending order

    def save_model(self, request, obj, form, change):
        # Automatically set the status before saving
        today = timezone.now().date()
        if obj.valid_from <= today <= obj.valid_to:
            obj.status = 'active'
        elif today < obj.valid_from:
            obj.status = 'inactive'
        else:
            obj.status = 'expired'
        super().save_model(request, obj, form, change)

    def get_actions(self, request):
        actions = super().get_actions(request)
        # Optionally remove some actions or add custom actions here
        return actions

admin.site.register(Coupon, CouponAdmin)

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1 