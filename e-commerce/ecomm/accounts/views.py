import decimal
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from products.models import Brand, Color, Order, OrderItem, Product, Category,ProductImage, Size, SubCategory
from products.forms import BrandForm, CategoryForm, ColorForm, ProductForm, ProductImageForm, SizeForm, SubCategoryForm
from .forms import AdminLoginForm, SignupForm, LoginForm
from django.contrib.auth import get_user_model
from django.conf import settings
from .forms import CustomPasswordResetForm, OTPVerificationForm, CustomSetPasswordForm
from .utils import generate_otp,send_otp_email
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetConfirmView
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from .models import Account
from wallet.models import Referral, WalletTransaction
from decimal import Decimal
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from django.db.models import Count, Sum
import calendar
from django.db.models import Q
from django.core.paginator import Paginator

def login_page(request):
    # Check if the user is already authenticated
    if request.user.is_authenticated:
        return redirect('product_page:shop')  # Redirect to the shop page or another desired page

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Debugging: Print email and password
            print(f"Email: {email}, Password: {password}")
            
            # Authenticate using email as username
            user = authenticate(request, username=email, password=password)
            
            # Debugging: Print the authenticated user
            print(f"Authenticated User: {user}")
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('product_page:shop')  # Redirect to your desired page
                else:
                    messages.error(request, 'Account is inactive.', extra_tags='login')
            else:
                messages.error(request, 'Invalid email or password.', extra_tags='login')
        else:
            messages.error(request, 'Please correct the errors below.', extra_tags='login')
    else:
        form = LoginForm()

    return render(request, 'accounts/login_page.html', {'form': form})

def admin_login(request):
    if request.method == 'POST':
        form = AdminLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user and user.is_active and user.is_staff:
                login(request, user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Invalid username or password for admin.')
        else:
            messages.error(request, 'Invalid username or password for admin.')

    form = AdminLoginForm()
    return render(request, 'accounts/admin_login.html', {'form': form})



def logout_view(request):
    auth_logout(request)
    return redirect('main_page:index')

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = False
            user.otp = generate_otp() 
            user.save()

            # Process referral code
            referral_code = form.cleaned_data.get('referral_code')
            if referral_code:
                referral = get_object_or_404(Referral, referral_code=referral_code)
                # Award credits to both the referrer and the referee
                user.wallet += Decimal('50.00')
                user.save()

                # Award credits to the referrer
                referrer = referral.user
                referrer.wallet += Decimal('50.00')
                referrer.save()

                # Log the transactions
                WalletTransaction.objects.create(user=user, transaction_type='Credit', amount=Decimal('50.00'), description='Referral credit')
                WalletTransaction.objects.create(user=referrer, transaction_type='Credit', amount=Decimal('50.00'), description='Referral bonus')

                # Update the referrer’s referred friends list
                referral.referred_friends.add(user)
                referral.save()

            # Create Referral object
            Referral.objects.create(user=user)

            # Send OTP email
            send_otp_email(user.email, user.otp)
           
            messages.success(request, 'OTP has been sent to your email address. Please verify.', extra_tags='otp')
            return redirect('verify_otp', user_id=user.pk, scenario='signup')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.capitalize()}: {error}')
    else:
        form = SignupForm()
    
    return render(request, 'accounts/signup.html', {'form': form})

def admin_dashboard(request):
    # Determine the time period for filtering orders
    filter_type = request.GET.get('filter', 'daily')  # Default to daily if no filter is provided

    # Define the aggregation function based on filter type
    if filter_type == 'monthly':
        truncate_func = TruncMonth
        months = [calendar.month_abbr[i] for i in range(1, 13)]  # List of month abbreviations
    elif filter_type == 'yearly':
        truncate_func = TruncYear
        months = []  # No need for month labels if filtering yearly
    else:  # Default to daily
        truncate_func = TruncDay
        months = []  # No need for month labels if filtering daily

    # Aggregate order data based on the selected filter
    aggregated_orders = (
        Order.objects
        .annotate(date=truncate_func('created_at'))
        .values('date')
        .annotate(order_count=Count('id'))
        .order_by('date')
    )

    # Prepare data for the chart
    if filter_type == 'monthly':
        # Create a dictionary to map months to counts
        monthly_data = {calendar.month_abbr[i]: 0 for i in range(1, 13)}
        for order in aggregated_orders:
            month_name = calendar.month_abbr[order['date'].month]
            monthly_data[month_name] = order['order_count']

        chart_labels = months
        chart_data = [monthly_data[month] for month in months]
    elif filter_type == 'yearly':
        chart_labels = [order['date'].strftime('%Y') for order in aggregated_orders]
        chart_data = [order['order_count'] for order in aggregated_orders]
    else:  # Default to daily
        chart_labels = [order['date'].strftime('%Y-%m-%d') for order in aggregated_orders]
        chart_data = [order['order_count'] for order in aggregated_orders]

    # Fetch most selling products data
    most_selling_products = (
        OrderItem.objects
        .values('product__title')
        .annotate(total_sales=Sum('quantity'))
        .order_by('-total_sales')[:10]  # Top 10 most selling products
    )

    # Prepare data for the most selling products chart
    product_labels = [item['product__title'] for item in most_selling_products]
    product_data = [item['total_sales'] for item in most_selling_products]

    most_selling_brands = (
        OrderItem.objects
        .values('product__brand__brand_name')
        .annotate(total_quantity=Count('quantity'))
        .order_by('-total_quantity')[:10]  # Get top 10 selling brands
    )
    brand_labels = [item['product__brand__brand_name'] for item in most_selling_brands]
    brand_data = [item['total_quantity'] for item in most_selling_brands]

    # Fetch all orders
    orders = Order.objects.all()
    total_sales = Order.objects.filter(status='Delivered').aggregate(total_sales=Sum('grand_total'))['total_sales'] or 0
    total_orders = Order.objects.count()
    active_users = get_user_model().objects.filter(is_active=True).count()
    total_products = Product.objects.count()
    delivered_orders = Order.objects.filter(status='Delivered').count()
    shipped_orders = Order.objects.filter(status='Shipped').count()
    cancelled_orders = Order.objects.filter(status='Cancelled').count()
    returned_orders = Order.objects.filter(status='Returned').count()
    context = {
        'orders': orders,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'product_labels': product_labels,
        'product_data': product_data,
        'brand_labels': brand_labels,
        'brand_data': brand_data,
        'selected_filter': filter_type,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'active_users': active_users,
        'total_products': total_products,
        'delivered_orders': delivered_orders,
        'shipped_orders': shipped_orders,
        'cancelled_orders': cancelled_orders,
        'returned_orders': returned_orders,
    }

    if request.user.is_authenticated and request.user.is_staff:
        return render(request, 'accounts/admin_dashboard.html', context)
    else:
        return redirect('main_page:index')
    

def admin_products(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    brands = Brand.objects.all()
    sizes = Size.objects.all()
    colors = Color.objects.all()

    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(title__icontains=search_query) |
            Q(original_price__icontains=search_query) |
            Q(product_offer__icontains=search_query) |
            Q(category__category_name__icontains=search_query) |
            Q(brand__brand_name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(products, 6)  # Show 6 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        category_form = CategoryForm(request.POST)
        brand_form = BrandForm(request.POST)
        size_form = SizeForm(request.POST)
        color_form = ColorForm(request.POST)

        if category_form.is_valid():
            category_form.save()
            messages.success(request, 'Category added successfully.', extra_tags='product_update')
            return redirect('admin_products')
        elif brand_form.is_valid():
            brand_form.save()
            messages.success(request, 'Brand added successfully.', extra_tags='product_update')
            return redirect('admin_products')
        elif size_form.is_valid():
            size_form.save()
            messages.success(request, 'Size added successfully.')
            return redirect('admin_products')
        elif color_form.is_valid():
            color_form.save()
            messages.success(request, 'Color added successfully.')
            return redirect('admin_products')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        category_form = CategoryForm()
        brand_form = BrandForm()
        size_form = SizeForm()
        color_form = ColorForm()

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'brands': brands,
        'sizes': sizes,
        'colors': colors,
        'category_form': category_form,
        'brand_form': brand_form,
        'size_form': size_form,
        'color_form': color_form,
        'search_query': search_query,
    }
    return render(request, 'admin_side/admin_products.html', context)

def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()
    existing_images = product.images.all()

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        image_form = ProductImageForm(request.POST, request.FILES)

        if form.is_valid():
            product_instance = form.save(commit=False)
            product_instance.updated_by = request.user  # Assuming you have an updated_by field
            product_instance.save()

            form.save_m2m()  # Save many-to-many data (sizes and colors)

            for image in existing_images:
                image_field_name = f'image_{image.id}'
                if image_field_name in request.FILES:
                    image.image = request.FILES[image_field_name]
                    image.save()

            messages.success(request, 'Product updated successfully.', extra_tags='product_update')
            return redirect('admin_products')
        else:
            messages.error(request, 'Please correct the errors below.', extra_tags='product_update')
    else:
        form = ProductForm(instance=product)
        image_form = ProductImageForm()

    return render(request, 'admin_side/edit_product.html', {
        'form': form, 
        'product': product, 
        'categories': categories, 
        'image_form': image_form,
        'existing_images': existing_images
    })





def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        # Update availability status instead of deleting
        if product.availability_status == 'in_stock':
            product.availability_status = 'out_of_stock'
        else:
            product.availability_status = 'in_stock'
        product.save()
        
        messages.success(request, f'Availability of "{product.title}" changed successfully.', extra_tags='product_update')
        return redirect('admin_products')  # Redirect to the product list page or wherever appropriate
    
    return render(request, 'admin_side/confirm_delete_product.html', {'product': product})


def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        # Toggle is_active status instead of deleting
        category.is_active = not category.is_active  # Assuming 'is_active' is a BooleanField
        category.save()
        
        messages.success(request, 'Category status changed successfully.', extra_tags='product_update')
        return redirect('product_categories')  # Redirect to the admin products page or appropriate view
    
    return render(request, 'admin_side/confirm_delete_category.html', {'category': category})

def toggle_brand_status(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    brand.is_active = not brand.is_active  # Toggle the status
    brand.save()
    return redirect('admin_products')



@login_required

def add_product(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST, request.FILES)

        if product_form.is_valid():
            product = product_form.save(commit=False)
            product.created_by = request.user
            product.save()
            product_form.save_m2m()

            # Handle main product image
            main_image = request.FILES.get('product_image')
            if main_image:
                print(f"Main image: {main_image.name}")
                ProductImage.objects.create(product=product, image=main_image, is_main=True)

            # Handle additional images
            additional_images = request.FILES.getlist('additional_images')
            for image in additional_images:
                print(f"Additional image: {image.name}")
                ProductImage.objects.create(product=product, image=image, is_main=False)

            messages.success(request, 'Product added successfully.')
            return redirect('admin_products')

    else:
        product_form = ProductForm()

    # Populate subcategories based on the selected category
    category_id = request.GET.get('category')
    if category_id:
        try:
            subcategories = SubCategory.objects.filter(category_id=category_id)
            product_form.fields['subcategories'].queryset = subcategories
        except SubCategory.DoesNotExist:
            product_form.fields['subcategories'].queryset = SubCategory.objects.none()

    return render(request, 'admin_side/add_products.html', {'product_form': product_form})




def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.', extra_tags='product_update')
            return redirect('admin_products')
        else:
            messages.error(request, 'Please correct the errors below.', extra_tags='product_update')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'admin_side/edit_category.html', {'form': form, 'category': category})

def edit_brand(request, pk):
    brand = get_object_or_404(Brand, pk=pk)

    if request.method == 'POST':
        form = BrandForm(request.POST, instance=brand)
        if form.is_valid():
            form.save()
            messages.success(request, 'Brand updated successfully.', extra_tags='product_update')
            return redirect('admin_products')
        else:
            messages.error(request, 'Please correct the errors below.', extra_tags='product_update')
    else:
        form = BrandForm(instance=brand)

    return render(request, 'admin_side/edit_brand.html', {'form': form, 'brand': brand})

def product_categories(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully.')
            return redirect('product_categories')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CategoryForm()
    return render(request, 'admin_side/product_categories.html', {
        'categories': categories,
        'category_form': form
    })

def manage_subcategories(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    subcategories = SubCategory.objects.filter(category=category)
    
    if request.method == 'POST':
        if 'subcategory_id' in request.POST:  # Check if we're updating an existing subcategory
            subcategory_id = request.POST.get('subcategory_id')
            subcategory = get_object_or_404(SubCategory, pk=subcategory_id)
            form = SubCategoryForm(request.POST, instance=subcategory)
        else:  # Adding a new subcategory
            form = SubCategoryForm(request.POST)
            form.instance.category = category  # Set the category from the context

        if form.is_valid():
            form.save()
            return redirect('manage_subcategories', category_id=category_id)

    else:
        form = SubCategoryForm()

    context = {
        'category': category,
        'subcategories': subcategories,
        'subcategory_form': form,
    }
    
    return render(request, 'admin_side/manage_subcategories.html', context)

def edit_subcategory(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)
    if request.method == 'POST':
        form = SubCategoryForm(request.POST, instance=subcategory)
        if form.is_valid():
            form.save()
            return redirect('manage_subcategories', category_id=subcategory.category.id)
    else:
        form = SubCategoryForm(instance=subcategory)
    
    context = {
        'form': form,
        'subcategory': subcategory,
    }
    return render(request, 'admin_side/edit_subcategory.html', context)

def delete_subcategory(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)
    if request.method == 'POST':
        subcategory.delete()
        return redirect('manage_subcategories', category_id=subcategory.category.id)
    else:
        # If not POST, redirect back to the manage subcategories page
        return redirect('manage_subcategories', category_id=subcategory.category.id)

def product_brands(request):
    brands = Brand.objects.all()
    if request.method == 'POST':
        form = BrandForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Brand added successfully.')
            return redirect('product_brands')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BrandForm()
    return render(request, 'admin_side/product_brands.html', {
        'brands': brands,
        'brand_form': form
    })


UserModel = get_user_model()

def forgot_password(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                #user = UserModel.objects.get(email=email)
                user = Account.objects.get(email=email)
                otp = generate_otp()
                user.otp = otp
                user.save()

                #send_otp_email(email, otp)
                send_otp_email(user.email, user.otp)
                messages.success(request, 'OTP has been sent to your email address.', extra_tags='otp')
                return redirect('verify_otp', user.pk, 'forgot_password')
            #except UserModel.DoesNotExist:
            except Account.DoesNotExist:
                messages.error(request, 'No account found with this email address.', extra_tags='otp')
    else:
        form = CustomPasswordResetForm()

    return render(request, 'accounts/forgot_password.html', {'form': form})

def verify_otp(request, user_id, scenario):
    try:
        user = UserModel.objects.get(pk=user_id)    
    except UserModel.DoesNotExist:
        messages.error(request, "Invalid user.")
        return redirect('login')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_entered = form.cleaned_data['otp']
            if user.otp == otp_entered:
                user.otp = None
                user.is_active = True
                user.save()
                
                if scenario == 'signup':
                    user.backend = 'django.contrib.auth.backends.ModelBackend'  # Set the authentication backend
                    auth_login(request, user)
                    messages.success(request, 'OTP verified successfully. Now you can log in.')
                    return redirect('login')
                elif scenario == 'forgot_password':
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    token = default_token_generator.make_token(user)
                    return redirect('password_reset_confirm', uidb64=uid, token=token)
            else:
                messages.error(request, "Invalid OTP entered.")
                #user = Account.objects.get(otp=otp_entered)
                #user.backend = 'django.contrib.auth.backends.ModelBackend'
                #login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                #uid = urlsafe_base64_encode(force_bytes(user.pk))
                #token = default_token_generator.make_token(user)
                #login(request, user)
                #messages.success(request, 'OTP verified successfully. You are now logged in.')
                #return redirect('password_reset_confirm', uidb64=uid, token=token)
               
    else:
        form = OTPVerificationForm(initial={'scenario': scenario})

    return render(request, 'accounts/verify_otp.html', {'form': form, 'user': user, 'scenario': scenario})


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('login')
    form_class = CustomSetPasswordForm


    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Password changed successfully. Now you can log in.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['uidb64'] = self.kwargs['uidb64']
        context['token'] = self.kwargs['token']
        return context
    

   

