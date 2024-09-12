from datetime import datetime, timedelta
from decimal import Decimal
import json
from django.utils import timezone
import uuid
from django.shortcuts import render, get_object_or_404
from .models import Cart, CartItem, Coupon, Order, OrderItem, Product, Category, Brand, ProductVariant, Size, Color, SubCategory
from django.core.paginator import Paginator
from django.shortcuts import render,redirect
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from User.models import Address, OrderAddress
from django.db.models import Count
from .forms import CouponForm, ProductVariantForm
from wallet.models import Referral, WalletTransaction
from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F, ExpressionWrapper, DecimalField, Count
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


def shop(request):
    search_query = request.GET.get('search', '')
    category_names = request.GET.getlist('category')
    subcategory_names = request.GET.getlist('subcategory')
    brand_names = request.GET.getlist('brand')
    colors = request.GET.getlist('color')
    sizes = request.GET.getlist('size')
    sort = request.GET.get('sort')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    cart_items_count = CartItem.objects.filter(cart__user=request.user).count()

    product_list = Product.objects.all()

    # Apply search filter
    if search_query:
        product_list = product_list.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(brand__brand_name__icontains=search_query) |
            Q(category__category_name__icontains=search_query) |
            Q(subcategory__subcategory_name__icontains=search_query) |
            Q(colors__color_name__icontains=search_query) |
            Q(sizes__size_name__icontains=search_query)
        ).distinct()

    # Apply category and subcategory filter
    if category_names:
        product_list = product_list.filter(category__category_name__in=category_names).distinct()
    
    if subcategory_names:
        product_list = product_list.filter(subcategory__subcategory_name__in=subcategory_names).distinct()

    # Apply brand filter
    if brand_names:
        product_list = product_list.filter(brand__brand_name__in=brand_names).distinct()

    # Apply color filter
    if colors:
        product_list = product_list.filter(colors__color_name__in=colors).distinct()

    # Apply size filter
    if sizes:
        product_list = product_list.filter(sizes__size_name__in=sizes).distinct()

    # Apply price range filter
    try:
        if min_price:
            product_list = product_list.filter(offer_price__gte=min_price)
        if max_price:
            product_list = product_list.filter(offer_price__lte=max_price)
    except ValueError:
        pass

    # Annotate products with purchase counts
    product_list = product_list.annotate(
        offer_price_field=ExpressionWrapper(
            F('original_price') * (1 - F('product_offer') / 100),
            output_field=DecimalField()
        ),
        cart_count=Count('cartitem')
    )


    # Apply sorting
    if sort == 'popularity':
        product_list = product_list.order_by('-cart_count')
    elif sort == 'price_low_high':
        product_list = product_list.order_by('offer_price_field')
    elif sort == 'price_high_low':
        product_list = product_list.order_by('-offer_price_field')
    elif sort == 'average_ratings':
        product_list = product_list.order_by('-rating')
    elif sort == 'featured':
        product_list = product_list.order_by('-featured')
    elif sort == 'new_arrivals':
        product_list = product_list.order_by('-created_at')
    elif sort == 'a_z':
        product_list = product_list.order_by('title')
    elif sort == 'z_a':
        product_list = product_list.order_by('-title')
    else:
        product_list = product_list.order_by('-created_at')

    # Paginate the product list
    product_paginator = Paginator(product_list, 6)
    page_number = request.GET.get('page')
    product_list = product_paginator.get_page(page_number)

    # Fetch categories, brands, sizes, and colors
    categories = Category.objects.filter(is_active=True).prefetch_related('subcategories')
    brands = Brand.objects.filter(is_active=True)
    sizes = Size.objects.all()
    colors = Color.objects.all()

    context = {
        'products': product_list,
        'categories': categories,
        'brands': brands,
        'sizes': sizes,
        'colors': colors,
        'selected_category': category_names,
        'selected_subcategory': subcategory_names,
        'selected_brand': brand_names,
        'selected_color': colors,
        'selected_size': sizes,
        'selected_sort': sort,
        'min_price': min_price,
        'max_price': max_price,
        'search_query': search_query,
        'cart_items_count': cart_items_count,
        'product_error': request.session.pop('product_error', None)
    }

    return render(request, 'shop.html', context)



def shop_single(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    features_products = Product.objects.filter(trending=True)[:3]

    # Get sizes and colors for the product
    sizes = product.sizes.all()
    colors = product.colors.all()

    # Calculate the offer price and the best offer
    offer_price = product.offer_price
    best_offer_percentage= product.get_best_offer()

    context = {
        'product': product,
        'featured_items': features_products,
        'sizes': sizes,
        'colors': colors,
        'offer_price': offer_price,
        'best_offer_percentage': best_offer_percentage,
        'availability_message': "Only 1 item left" if product.quantity == 1 else "",
    }
    return render(request, 'shop-single.html', context)

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Get the quantity, size, and color from the POST request
    quantity = int(request.POST.get('quantity', 1))
    size_id = request.POST.get('size')
    color_id = request.POST.get('color')
    
    # Retrieve size and color if provided
    size = Size.objects.get(id=size_id) if size_id else None
    color = Color.objects.get(id=color_id) if color_id else None
    
    # Check if there is enough stock available
    if quantity > product.quantity:
        messages.error(request, 'Not enough stock available.')
        return redirect('product_page:shop-single', product_id=product.id)
    
    # Check if the cart item already exists
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart, product=product, size=size, color=color
    )
    
    if not item_created:
        if cart_item.quantity + quantity > product.quantity:
            messages.error(request, 'Not enough stock available to add this quantity.')
            return redirect('product_page:shop-single', product_id=product.id)
        
        if cart_item.quantity + quantity > product.max_qty_per_person:
            messages.error(request, f'You can only add up to {product.max_qty_per_person} items of this product.')
            return redirect('product_page:shop-single', product_id=product.id)
        
        cart_item.quantity += quantity
        cart_item.save()
    else:
        if quantity > product.max_qty_per_person:
            messages.error(request, f'You can only add up to {product.max_qty_per_person} items of this product.')
            return redirect('product_page:shop-single', product_id=product.id)
        
        cart_item.quantity = quantity
        cart_item.save()
    
    referrer = request.META.get('HTTP_REFERER', '')
    if 'shop-single' in referrer:
        return redirect('product_page:cart')
    
    return redirect('product_page:shop')

def cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    cart_items_count = cart_items.count()
    
    # Retrieve any product error message from the session
    product_error = request.session.pop('product_error', None)

    
    
    context = {
        'cart_items': cart_items,
        'total': sum(item.total_price for item in cart_items),
        'cart_items_count': cart_items_count,
        'product_error': product_error
    }
    
    return render(request, 'cart.html', context)

def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
    cart_item.delete()
   
    return redirect('product_page:cart')




def product_filter_by_size(request):
    size = request.GET.get('size')
    products = Product.objects.filter(sizes__size_name=size)
    small_count = Product.objects.filter(sizes__size_name='Small').count()
    medium_count = Product.objects.filter(sizes__size_name='Medium').count()
    large_count = Product.objects.filter(sizes__size_name='Large').count()
    context = {
        'products': products,
        'selected_size': size,  
        'small_count': small_count,
        'medium_count': medium_count,
        'large_count': large_count,
        }
    
    return render(request, 'shop.html', context)

def product_filter_by_color(request):
    color = request.GET.get('color')
    products = Product.objects.filter(colors__color_name=color)
    context = {'products': products}
    return render(request, 'shop.html', context)


def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    today = timezone.now().date()
    coupons = Coupon.objects.all()
    for coupon in coupons:
        coupon.update_status()
        coupon.save()  # Save the coupon to apply the status update

    # Fetch active coupons
    active_coupons = Coupon.objects.filter(status='active', valid_from__lte=today, valid_to__gte=today)
    # Calculate total and shipping fee
    total = sum(item.offer_price * item.quantity for item in cart_items)
    shipping_fee = 50 if total <= 350 else 0

    # Initialize variables for coupon and referral code processing
    coupon_code = request.POST.get('coupon_code', '').strip()
    referral_code = request.POST.get('referral_code', '').strip()
    remove_coupon = request.POST.get('remove_coupon', '') == 'true'
    discount = Decimal('0.00')
    discount_amount = Decimal('0.00')
    referral_discount_amount = Decimal('0.00')
    message = "Coupon code applied successfully."
    success = True
    applied_coupon_code = None

    if remove_coupon:
        coupon_code = None  # If removing coupon, clear the code

    # Handle coupon code
    if coupon_code:
        #print(f"Coupon code received: {coupon_code}")
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            #print(f"Coupon found: {coupon}")
            coupon.update_status()  # Make sure this method updates coupon status
            #print(f"Coupon status after update: {coupon.status}")
            coupon.save()
            if coupon.status == 'active':
                discount = coupon.discount
                discount_amount = (total * discount / 100)
                applied_coupon_code = coupon_code
                #print(f"Discount applied: {discount_amount} (Discount: {discount}%)")
                request.session['applied_coupon_code'] = applied_coupon_code

            else:
                message = "Invalid or expired coupon code."
                success = False
                #print(f"Message: {message}")
        except Coupon.DoesNotExist:
            message = "Coupon code does not exist."
            success = False
            #print(f"Message: {message}")

    if remove_coupon:
        request.session['applied_coupon_code'] = None
        discount_amount = Decimal('0.00')
        message = "Coupon removed successfully."
        #print(f"Discount amount after removal: {discount_amount}")

    grand_total = total + shipping_fee - discount_amount
    #print(f"Total: {total}, Shipping Fee: {shipping_fee}, Discount Amount: {discount_amount}")
    #print(f"Grand Total: {grand_total}")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        response_data = {
            'success': success,
            'message': message,
            'new_total': grand_total,
            'shipping_fee': shipping_fee,
            'discount_amount': discount_amount,
            'referral_discount_amount': referral_discount_amount,
            'applied_coupon_code': applied_coupon_code,
            'discount': discount
        }
        return JsonResponse(response_data)

    # Calculate estimated delivery date
    delivery_days = 5
    estimated_delivery_date = timezone.now() + timedelta(days=delivery_days)
    formatted_delivery_date = estimated_delivery_date.strftime('%d %b %Y')

    # Retrieve addresses for the user
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')

    if request.method == 'POST':
        address_id = request.POST.get('selected_address')
        payment_method = request.POST.get('payment_method')

        # Validate address and payment method
        if not address_id:
            messages.error(request, "Please select a shipping address.")
            return redirect('product_page:checkout')

        if not payment_method:
            messages.error(request, "Please select a payment method.")
            return redirect('product_page:checkout')

        try:
            selected_address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            messages.error(request, "Selected address does not exist.")
            return redirect('product_page:checkout')
        
        order_address = OrderAddress.objects.create(
            first_name=selected_address.first_name,
            last_name=selected_address.last_name,
            phone_number=selected_address.phone_number,
            street_address=selected_address.street_address,
            city=selected_address.city,
            state=selected_address.state,
            country=selected_address.country,
            postal_code=selected_address.postal_code,
            email=selected_address.email
        )

        formatted_address = (f"{selected_address.first_name} {selected_address.last_name}, "
                              f"{selected_address.street_address}, {selected_address.city}, "
                              f"{selected_address.state}, {selected_address.country}, "
                              f"{selected_address.postal_code}")

        # Store data in session
        cart_items_data = [
            {
                'title': item.product.title,
                'quantity': item.quantity,
                'total_price': float(item.total_price)
            } for item in cart_items
        ]
        request.session['cart_items'] = cart_items_data
        request.session['total'] = float(total)
        request.session['shipping_fee'] = float(shipping_fee)
        request.session['grand_total'] = float(grand_total)
        request.session['selected_address'] = {
            'address': formatted_address,
            'id': selected_address.id,
            'payment_method': payment_method,
        }
        request.session['estimated_delivery_date'] = formatted_delivery_date
        request.session['order_address_id'] = order_address.id

        # Redirect based on payment method
        if payment_method == 'RazorPay':
            return redirect('product_page:razorpaycheck')
        elif payment_method == 'COD':
            return redirect('product_page:order_summary')
        elif payment_method == 'Wallet':
            return redirect('product_page:order_summary')  
        else:
            messages.error(request, "Invalid payment method selected.")
            return redirect('product_page:checkout')

    context = {
        'cart_items': cart_items,
        'total': total,
        'shipping_fee': shipping_fee,
        'grand_total': grand_total,
        'addresses': addresses,
        'formatted_delivery_date': formatted_delivery_date,
        'referral_discount_amount': referral_discount_amount, 
        'coupons': active_coupons,
    }

    return render(request, 'user/checkout.html', context)






def update_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 0))

        try:
            cart = Cart.objects.get(user=request.user)
            item = CartItem.objects.get(cart=cart, id=item_id)
            product = item.product

            # Check if quantity exceeds stock
            if quantity > product.quantity:
                return JsonResponse({'success': False, 'error_message': f"Not enough stock available for {product.title}."})
            # Check if quantity exceeds maximum allowed per person
            elif quantity > product.max_qty_per_person:
                return JsonResponse({'success': False, 'error_message': f"Quantity exceeds limit for {product.title}."})
            else:
                item.quantity = quantity
                item.save()
                return JsonResponse({'success': True})

        except Cart.DoesNotExist:
            return JsonResponse({'success': False, 'error_message': 'Cart not found.'})
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'error_message': 'Cart item not found.'})
        except ValueError:
            return JsonResponse({'success': False, 'error_message': 'Invalid quantity.'})

    return JsonResponse({'success': False, 'error_message': 'Invalid request method'}, status=405)

def place_order(request):
    if request.method == 'POST':
        # Retrieve session data
        cart_items_data = request.session.get('cart_items', [])
        total = Decimal(request.session.get('total', '0'))
        shipping_fee = Decimal(request.session.get('shipping_fee', '0'))
        grand_total = Decimal(request.session.get('grand_total', '0'))
        selected_address = request.session.get('selected_address', {})
        address_id = selected_address.get('id')
        payment_method = selected_address.get('payment_method')
        payment_id = request.POST.get('payment_id')
        coupon_code = request.session.get('applied_coupon_code', None)

        if not cart_items_data or not address_id:
            return JsonResponse({'status': "Incomplete order details"}, status=400)

        try:
            # Retrieve the address from the database
            selected_address_instance = Address.objects.get(id=address_id)

            # Create the OrderAddress instance
            # order_address = OrderAddress.objects.create(
            #     first_name=selected_address_instance.first_name,
            #     last_name=selected_address_instance.last_name,
            #     phone_number=selected_address_instance.phone_number,
            #     street_address=selected_address_instance.street_address,
            #     city=selected_address_instance.city,
            #     state=selected_address_instance.state,
            #     country=selected_address_instance.country,
            #     postal_code=selected_address_instance.postal_code,
            #     email=selected_address_instance.email
            # )
            order_address_id = request.session.get('order_address_id')
            if not order_address_id:
                return JsonResponse({'status': "Order address not found in session."}, status=400)

            try:
                order_address = OrderAddress.objects.get(id=order_address_id)
            except OrderAddress.DoesNotExist:
                return JsonResponse({'status': "Order address does not exist."}, status=400)

            # Retrieve coupon if available
            coupon = None
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code)
                except Coupon.DoesNotExist:
                    coupon = None

            # Create the order
            order = Order.objects.create(
                user=request.user,
                address=order_address,
                payment_method=payment_method,
                total_amount=total,
                shipping_fee=shipping_fee,
                grand_total=grand_total,
                order_number=str(uuid.uuid4()),
                status='Ordered',
                payment_id=payment_id,
                payment_status='Pending',
                coupon=coupon if coupon else None
            )

            # Process cart items
            for item_data in cart_items_data:
                product = Product.objects.get(title=item_data['title'])
                if product.quantity < item_data['quantity']:
                    return JsonResponse({'status': f"Insufficient stock for product {product.title}."}, status=400)

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item_data['quantity'],
                    total_price=Decimal(item_data['total_price'])
                )

                # Update product quantity and popularity
                product.quantity -= item_data['quantity']
                product.popularity += item_data['quantity']
                product.save()

            # Clear the cart
            CartItem.objects.filter(cart__user=request.user).delete()

            # Handle wallet payment
            if payment_method == 'Wallet':
                user = request.user
                if user.wallet < grand_total:
                    return JsonResponse({'status': "Insufficient wallet balance."}, status=400)

                # Deduct the amount from the wallet
                user.wallet -= grand_total
                user.save()

                # Create wallet transaction record
                WalletTransaction.objects.create(
                    user=user,
                    transaction_type='Debit',
                    amount=grand_total,
                    description=f'Order #{order.order_number} payment'
                )

                # Update order status and payment status
                order.wallet_credit = grand_total
                order.payment_status = 'Completed'
                order.save()

            return redirect('product_page:order_success', order_number=order.order_number)

        except Address.DoesNotExist:
            return JsonResponse({'status': "Selected address does not exist."}, status=400)
        except Product.DoesNotExist:
            return JsonResponse({'status': "Product does not exist."}, status=400)
        except Exception as e:
            return JsonResponse({'status': f"An error occurred while placing the order: {e}"}, status=500)
        

def order_summary(request):
    cart_items = request.session.get('cart_items', [])
    total = request.session.get('total', 0)
    shipping_fee = request.session.get('shipping_fee', 0)
    grand_total = request.session.get('grand_total', 0)
    selected_address = request.session.get('selected_address', {})

    # Extract address details
    formatted_address = selected_address.get('address', 'No address selected')
    payment_method = selected_address.get('payment_method', 'Not Provided')
    

    context = {
        'cart_items': cart_items,
        'total': total,
        'shipping_fee': shipping_fee,
        'grand_total': grand_total,
        'formatted_address': formatted_address,
        'payment_method': payment_method,
    }

    return render(request, 'user/order_summary.html', context)



def order_success(request, order_number):
    # Fetch the order using the order_number
    order = get_object_or_404(Order, order_number=order_number)


    

    # Update the payment status to completed and order status to ordered if necessary
    # if order.payment_status == 'Pending':
    #     order.payment_status = 'Completed'
    #     order.status = 'Ordered'
    #     order.save()

    # Clear the cart for the user
    cart_items = CartItem.objects.filter(cart__user=request.user)
    cart_items.delete()
    
    # Decrement product quantities
    # for item in order.items.all():
    #     product = item.product
    #     if product.quantity >= item.quantity:
    #         product.quantity -= item.quantity
    #         product.save()
    #     else:
    #         # Handle the case where stock is insufficient, if needed
    #         pass

    context = {
        'order': order,
        'order_number': order_number,
    }

    return render(request, 'user/order_success.html', context)

def order_success_after_failure(request, order_number):
    # Fetch the order using the order_number
    order = get_object_or_404(Order, order_number=order_number)

    if order.payment_method == 'RazorPay' and order.payment_status == 'Pending':
            order.status = 'Ordered'
            order.payment_status = 'Completed'
            order.save()

    
    # Ensure the order was pending and now update to completed
    if order.payment_method == 'COD' and order.payment_status == 'Pending':
        order.payment_status = 'Completed'
        order.status = 'Ordered'
        order.save()
        

    # Clear the cart for the user
    cart_items = CartItem.objects.filter(cart__user=request.user)
    cart_items.delete()

    context = {
        'order': order,
        'order_number': order_number,
    }

    return render(request, 'user/order_success_after_failure.html', context)




def coupon_list(request):
    search_query = request.GET.get('search', '')

    if search_query:
        coupon_list = Coupon.objects.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query)
        )
    else:
        coupon_list = Coupon.objects.all()

    paginator = Paginator(coupon_list, 3)  # Show 3 coupons per page

    page = request.GET.get('page')
    try:
        coupons = paginator.page(page)
    except PageNotAnInteger:
        coupons = paginator.page(1)
    except EmptyPage:
        coupons = paginator.page(paginator.num_pages)

    context = {
        'coupons': coupons,
        'search_query': search_query,
    }
    return render(request, 'admin_side/coupon_list.html', context)

def coupon_add(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_page:coupon_list')
    else:
        form = CouponForm()
    return render(request, 'admin_side/coupon_form.html', {'form': form})

def coupon_edit(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            return redirect('product_page:coupon_list')
    else:
        form = CouponForm(instance=coupon)
    return render(request, 'admin_side/coupon_form.html', {'form': form})

def coupon_delete(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)

    # Directly update the status field
    if coupon.status == 'active':
        coupon.status = 'inactive'
    else:
        coupon.status = 'active'
    
    coupon.save(update_fields=['status'])  # Use update_fields to only save the status field

    return redirect('product_page:coupon_list')


def list_product_variants(request):
    variants = ProductVariant.objects.all()
    return render(request, 'admin_side/product_variants.html', {'variants': variants})

def add_product_variant(request):
    if request.method == 'POST':
        form = ProductVariantForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('product_page:list_product_variants'))
    else:
        form = ProductVariantForm()
    return render(request, 'admin_side/product_variants_form.html', {'form': form})

def edit_product_variant(request, pk):
    variant = get_object_or_404(ProductVariant, pk=pk)
    if request.method == 'POST':
        form = ProductVariantForm(request.POST, instance=variant)
        if form.is_valid():
            form.save()
            return redirect(reverse('product_page:list_product_variants'))
    else:
        form = ProductVariantForm(instance=variant)
    return render(request, 'admin_side/product_variants_form.html', {'form': form})

def delete_product_variant(request, pk):
    variant = get_object_or_404(ProductVariant, pk=pk)
    if request.method == 'POST':
        variant.delete()
        return redirect(reverse('product_page:list_product_variants'))
    return render(request, 'confirm_delete.html', {'object': variant})


@csrf_exempt 
def razorpaycheck(request):
    if request.method == "POST":
        try:
            #print("Received POST request in razorpaycheck")

            data = json.loads(request.body)
            #print("Parsed JSON data:", data)

            selected_address = data.get('selected_address')
            payment_method = data.get('payment_method')
            #print(f"Selected Address: {selected_address}, Payment Method: {payment_method}")

            cart = Cart.objects.filter(user=request.user).first()
            total_price = sum(item.total_price for item in CartItem.objects.filter(cart=cart))
            shipping_fee = 50 if total_price <= 350 else 0
            #print(f"Total Price: {total_price}, Shipping Fee: {shipping_fee}")

            coupon_code = request.session.get('applied_coupon_code', None)
            #print(f"Coupon Code from Session: {coupon_code}")

            discount_amount = Decimal('0.00')
            coupon = None
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code)
                    if coupon.status == 'active':
                        discount_amount = total_price * coupon.discount / 100
                        #print(f"Coupon Applied: {coupon_code}, Discount Amount: {discount_amount}")
                    else:
                        # If coupon is inactive, clear it from the session
                        request.session.pop('applied_coupon_code', None)
                        #print(f"Coupon code {coupon_code} is inactive. Clearing coupon.")
                except Coupon.DoesNotExist:
                    # If coupon does not exist, clear it from the session
                    request.session.pop('applied_coupon_code', None)
                    #print(f"Coupon code {coupon_code} does not exist. Clearing coupon.")


            grand_total = total_price + shipping_fee - discount_amount
            #print(f"Grand Total after discount: {grand_total}")

            

            address = Address.objects.filter(user=request.user).first()
            if not address:
                #print("No address found for the user")
                return JsonResponse({'error': 'No address found for the user'}, status=400)
            
            order_address_id = request.session.get('order_address_id')
            if not order_address_id:
                return JsonResponse({'status': "Order address not found in session."}, status=400)

            try:
                order_address = OrderAddress.objects.get(id=order_address_id)
            except OrderAddress.DoesNotExist:
                return JsonResponse({'status': "Order address does not exist."}, status=400)

            order = Order.objects.create(
                user=request.user,
                address=order_address,
                payment_method='RazorPay',
                total_amount=total_price,
                shipping_fee=shipping_fee,
                grand_total=grand_total,
                order_number=str(uuid.uuid4()),
                status='Pending',
                coupon=coupon  # Set coupon if valid, else None
            )
            #print(f"Order created with ID: {order.order_number}")

            cart_items = CartItem.objects.filter(cart=cart)
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    total_price=cart_item.total_price,
                )
            

            request.session.pop('applied_coupon_code', None)
           

            return JsonResponse({
                'total_price': grand_total,
                'first_name': request.user.first_name,
                'email': request.user.email,
                'phone_number': request.user.phone_number,
                'order_id': order.order_number,
                
            })
        except json.JSONDecodeError:
            #print("Invalid JSON")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            #print(f"An error occurred: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    #print("Invalid request method")
    return JsonResponse({'error': 'Invalid request method'}, status=405)



def confirm_order_razorpay(request):
    if request.method == 'POST':
        try:
            #print("Received POST request in confirm_order_razorpay")

            data = json.loads(request.body)
            order_number = data.get('order_id')
            payment_id = data.get('payment_id')
            #print(f"Order ID: {order_number}, Payment ID: {payment_id}")

            order = get_object_or_404(Order, order_number=order_number)
            #print(f"Found order: {order.order_number}")

            if order.payment_method == 'COD':
                order.payment_status = 'Completed'
                order.save()
                #print(f"COD payment completed for order {order.order_number}")

                cart_items = CartItem.objects.filter(cart__user=request.user)
                for cart_item in cart_items:
                    product = cart_item.product
                    if product.quantity < cart_item.quantity:
                        #print(f"Insufficient stock for product {product.title}")
                        return JsonResponse({'status': f"Insufficient stock for product {product.title}."}, status=400)
                    product.quantity -= cart_item.quantity
                    product.popularity += cart_item.quantity
                    product.save()
                    #print(f"Updated product stock and popularity: {product.title}")

                    OrderItem.objects.update_or_create(
                        order=order,
                        product=product,
                        defaults={'quantity': cart_item.quantity, 'total_price': cart_item.total_price}
                    )
                    #print(f"Updated or created order item for product: {product.title}")

                cart_items.delete()
                return JsonResponse({'status': 'Order placed successfully', 'order_number': order.order_number})

            elif order.payment_method == 'RazorPay':
                order.payment_id = payment_id
                order.payment_status = 'Completed'
                order.status = 'Ordered'
                order.save()
                #print(f"RazorPay payment completed for order {order.order_number}")

                cart_items = CartItem.objects.filter(cart__user=request.user)
                for cart_item in cart_items:
                    product = cart_item.product
                    if product.quantity < cart_item.quantity:
                        #print(f"Insufficient stock for product {product.title}")
                        return JsonResponse({'status': f"Insufficient stock for product {product.title}."}, status=400)
                    product.quantity -= cart_item.quantity
                    product.popularity += cart_item.quantity
                    product.save()
                    #print(f"Updated product stock and popularity: {product.title}")

                    OrderItem.objects.update_or_create(
                        order=order,
                        product=product,
                        defaults={'quantity': cart_item.quantity, 'total_price': cart_item.total_price}
                    )
                    #print(f"Updated or created order item for product: {product.title}")

                cart_items.delete()
                return JsonResponse({'status': 'Order placed successfully', 'order_number': order.order_number})

        except json.JSONDecodeError:
            #print("Invalid JSON data")
            return JsonResponse({'status': 'Invalid JSON data'}, status=400)
        except Exception as e:
            #print(f"An error occurred: {str(e)}")
            return JsonResponse({'status': f"An error occurred: {str(e)}"}, status=500)
    else:
        #print("Invalid request method")
        return JsonResponse({'status': 'Invalid request method'}, status=405)


def order_failed(request):
    return render(request, 'user/order_failed.html')