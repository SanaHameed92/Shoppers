# products/forms.py

from django import forms
from .models import Coupon, Product, ProductImage, Category, Brand, ProductVariant, Size, Color, SubCategory

class ProductForm(forms.ModelForm):
    sizes = forms.ModelMultipleChoiceField(
        queryset=Size.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    colors = forms.ModelMultipleChoiceField(
        queryset=Color.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    

   
    
    class Meta:
        model = Product
        fields = [
            'title', 'description', 'category','subcategory', 'original_price','product_offer', 'rating', 'brand',
            'quantity','max_qty_per_person', 'trending', 'product_image','availability_status','sizes','colors','featured',
            
        ]

    def clean_original_price(self):
        original_price = self.cleaned_data.get('original_price')
        if original_price < 0:
            raise forms.ValidationError("Original price cannot be negative.")
        return original_price

    def clean_product_offer(self):
        product_offer = self.cleaned_data.get('product_offer')
        if product_offer < 0 or product_offer >= 100:
            raise forms.ValidationError("Product offer must be between 0 and 100 percent.")
        return product_offer



class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_name','category_offer','is_active']


    def clean_category_offer(self):
        category_offer = self.cleaned_data.get('category_offer')
        if category_offer < 0 or category_offer >= 100:
            raise forms.ValidationError("Category offer must be between 0 and 100 percent.")
        return category_offer
    
class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ['subcategory_name']
        widgets = {
            'subcategory_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter subcategory name'}),
        }

   

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['brand_name','brand_offer']

    def clean_brand_offer(self):
        brand_offer = self.cleaned_data.get('brand_offer')
        if brand_offer < 0 or brand_offer >= 100:
            raise forms.ValidationError("Brand offer must be between 0 and 100 percent.")
        return brand_offer

class SizeForm(forms.ModelForm):
    class Meta:
        model = Size
        fields = ['size_name']

class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ['color_name']

class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['product','size', 'color', 'quantity', 'quantity','price']


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']
        

class CartUpdateForm(forms.Form):

    def __init__(self, *args, **kwargs):
        cart_items = kwargs.pop('cart_items', [])
        super().__init__(*args, **kwargs)
        for item in cart_items:
            self.fields[f'quantity_{item.id}'] = forms.IntegerField(
                initial=item.quantity,
                min_value=1,
                max_value=item.product.max_qty_per_person,
                label=item.product.title
            )

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'name', 'discount', 'valid_from', 'valid_to']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['valid_from'].widget = forms.SelectDateWidget(years=range(2000, 2031))
        self.fields['valid_to'].widget = forms.SelectDateWidget(years=range(2000, 2031))