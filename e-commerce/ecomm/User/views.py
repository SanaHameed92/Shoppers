#User/views.py
from uuid import uuid4
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch, reverse
from .models import Address, Wishlist
from .forms import AddressForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from products.models import Order, OrderItem, Product
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.core.exceptions import MultipleObjectsReturned
from wallet.models import CancellationRequest, ReturnRequest, WalletTransaction
from django.db.models import Q  
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from decimal import Decimal, InvalidOperation

User = get_user_model()

@login_required
def personal_information(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')

        # Retrieve the current user instance
        user = request.user

        # Update the user instance with new data
        user.first_name = first_name
        user.last_name = last_name
        user.phone_number = phone_number

        # Save the updated user instance
        user.save()

        # Optionally, show a success message
        messages.success(request, 'Your personal information has been updated.',extra_tags='profile')

        # Redirect back to the personal information page or any other desired page
        return redirect('personal_information')

    # If it's a GET request, render the personal information form page
    return render(request, 'user/profile.html')

# Create your views here.
def profile(request):
    user = request.user
    return render(request, 'user/profile.html',{'user':user})

def manage_address(request):
    # Ensure user is authenticated
    if not request.user.is_authenticated:
        return redirect('login')  # Redirect to login if not authenticated

    # Filter addresses for the logged-in user
    addresses = Address.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'user/manage_address.html', {'addresses': addresses})

def add_address(request):
    redirect_url = request.GET.get('redirect_to', 'manage_address').strip()  # Default to 'manage_address'
    
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if redirect_url == 'product_page:checkout':
                address.is_default = True  # Set as default if coming from checkout
                Address.objects.filter(user=request.user).update(is_default=False)  # Make all others non-default
            address.save()
            messages.success(request, 'Address added successfully!')
            try:
                return redirect(reverse(redirect_url) if ':' in redirect_url else redirect_url)
            except NoReverseMatch:
                return redirect('manage_address')
    else:
        form = AddressForm()
    
    return render(request, 'user/add_address.html', {'form': form, 'redirect_url': redirect_url})




@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            return redirect('manage_address')
    else:
        form = AddressForm(instance=address)
    
    return render(request, 'user/edit_address.html', {'form': form})

@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id)
    if request.method == 'POST':
        address.delete()
        return redirect('manage_address')
    
    return render(request, 'user/delete_address.html', {'address': address})

def reset_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            new_password1 = form.cleaned_data['new_password1']
            new_password2 = form.cleaned_data['new_password2']
            if new_password1 == new_password2:
                user = form.save()
                update_session_auth_hash(request, user)  # Important to update the session
                messages.success(request, 'Your password was successfully updated!',extra_tags='profile')
                return redirect('personal_information')  # Redirect to profile page
            else:
                messages.error(request, "Passwords do not match. Please enter matching passwords.",extra_tags='profile')
        else:
            messages.error(request, 'Please enter correct password.',extra_tags='profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'user/profile.html', {'form': form})

def my_orders(request):
    query = request.GET.get('search', '')
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    if query:
        orders = orders.filter(
            Q(order_number__icontains=query) |
            Q(status__icontains=query) |
            Q(payment_status__icontains=query) |
            Q(payment_method__icontains=query)
        )
    return render(request, 'user/my_orders.html', {'orders': orders,'search_query': query})

def delete_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Order has been deleted successfully.')
        return redirect('my_orders')
    return render(request, 'user/my_orders.html', {'order': order})


def order_detail(request, order_number):
    try:
        order = Order.objects.get(order_number=order_number)
        print(f"Order found: {order}") 

        amount_saved = 0
        if order.coupon:
            discount = order.coupon.discount
            amount_saved = (order.total_amount * discount / 100)
      
        cancellation_request = CancellationRequest.objects.filter(order=order).first()
        order_items = OrderItem.objects.filter(order=order)
        print(f"Cancellation Request found: {cancellation_request}")
        
        can_continue_payment = (
            order.status == 'Pending' or 
            (order.status == 'Ordered' and order.payment_method == 'COD')
        )
    except Order.DoesNotExist:
        return render(request, 'user/order_not_found.html')

    context = {
        'order': order,
        'order_items': order_items,
        'can_continue_payment': can_continue_payment,
        'cancellation_request': cancellation_request,
        'amount_saved': amount_saved,
       
    }
    return render(request, 'user/order_detail.html', context)


def cancel_order(request, order_number):
    # Fetch the order for the current user
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    # Check if the order is not already cancelled
    if order.status != 'Cancelled':
        # Update the status to 'Cancelled'
        order.status = 'Cancelled'
       
        
        # Restore product quantities
        for item in order.items.all():
            product = item.product
            print(f"Before: {product.title} - Quantity: {product.quantity}")
            product.quantity += item.quantity
            print(f"After: {product.title} - Quantity: {product.quantity}")
            product.save()

        if order.payment_method == 'Wallet':
            # Credit the wallet if payment was done with wallet
            user = request.user
            user.wallet += order.grand_total
            user.save()
            order.status = 'Cancelled'
            order.wallet_credit = order.grand_total  
            order.payment_status = 'Refunded'
            order.save()
            
            # Log the wallet transaction
            WalletTransaction.objects.create(
                user=user,
                transaction_type='Credit',
                amount=order.grand_total,
                description=f'Refund for cancelled order {order.order_number}'
            )
            
            messages.success(request, "Order cancelled successfully! Refund credited to wallet.", extra_tags='order')
        
        # Process the refund if payment method is RazorPay
        elif order.payment_method == 'RazorPay':
            user = request.user
            user.wallet += order.grand_total
            user.save()
            order.wallet_credit = order.grand_total 
            order.payment_status = 'Refunded' 
            order.save()
            
            # Log the wallet transaction
            WalletTransaction.objects.create(
                user=user,
                transaction_type='Credit',
                amount=order.grand_total,
                description=f'Refund for cancelled order {order.order_number}'
            )
            
            messages.success(request, "Order cancelled successfully! Refund credited to wallet.", extra_tags='order')
        else:
            order.save()
            messages.success(request, "Order cancelled successfully!", extra_tags='order')
    else:
        # If the order is already cancelled, display an info message
        messages.info(request, "Order is already cancelled.", extra_tags='order')
    
    # Redirect to the order detail or any other page you prefer
    return redirect('order_detail', order_number=order_number)

def order_list(request):
    search_query = request.GET.get('search', '')
    cancellation_requests = CancellationRequest.objects.all()
    return_requests = ReturnRequest.objects.all()

    if search_query:
        try:
            # Try to handle numeric searches
            numeric_query = Decimal(search_query)
            numeric_filters = Q(shipping_fee=numeric_query) | Q(grand_total=numeric_query)
        except (ValueError, InvalidOperation):
            numeric_filters = Q()  # No numeric filters if conversion fails

        # Text search filters
        text_filters = Q(
            order_number__icontains=search_query) | \
            Q(user__username__icontains=search_query) | \
            Q(payment_method__icontains=search_query) | \
            Q(payment_status__icontains=search_query) | \
            Q(status__icontains=search_query)
        
        address_filters = Q(
            address__first_name__icontains=search_query) | \
            Q(address__last_name__icontains=search_query) | \
            Q(address__street_address__icontains=search_query) | \
            Q(address__city__icontains=search_query) | \
            Q(address__state__icontains=search_query) | \
            Q(address__country__icontains=search_query) | \
            Q(address__postal_code__icontains=search_query)
        
        order_list = Order.objects.filter(
            text_filters | numeric_filters | address_filters
        ).order_by('-created_at')
    else:
        order_list = Order.objects.all().order_by('-created_at')

    paginator = Paginator(order_list, 6)  # Show 6 orders per page

    page = request.GET.get('page')
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)

    context = {
        'orders': orders,
        'search_query': search_query,
        'cancellation_requests': cancellation_requests,
        'return_requests': return_requests,
    }
    return render(request, 'admin_side/order_list.html', context)


def order_detail_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    cancellation_request = CancellationRequest.objects.filter(order=order).first()
    return_request = ReturnRequest.objects.filter(order=order).first()
    context = {
        'order': order,
        'cancellation_request': cancellation_request,
        'return_request': return_request,
    }
    return render(request, 'admin_side/order_detail.html', context)

@require_POST
def update_order_status(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        order = get_object_or_404(Order, id=order_id)
        valid_statuses = ['Ordered', 'Shipped', 'Delivered', 'Cancelled', 'Refunded']
        if new_status not in valid_statuses:
            messages.error(request, "Invalid status update.")
            return redirect('order_list')
        
        # Implement custom logic for certain statuses
        if new_status == 'Cancelled':
            # Handle cancellation logic, e.g., refunds, inventory updates, etc.
            pass
        elif new_status == 'Ordered' and order.payment_method == 'COD':
            # Handle logic for delivered status, e.g., payment confirmation
            new_status = 'Completed'
        elif new_status == 'Delivered' and order.payment_method == 'COD':
            order.payment_status = 'Completed'
        order.status = new_status
        order.save()
    return redirect('order_list')

def add_to_wishlist(request, product_id):
    if not request.user.is_authenticated:
        messages.error(request, 'You need to be logged in to add items to your wishlist.', extra_tags='wishlist')
        return redirect('login')  # Redirect to login page

    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)

    if created:
        message = 'Product added to your wishlist.'
        messages.success(request, message, extra_tags='wishlist')
        success = True
    else:
        message = 'Product is already in your wishlist.'
        messages.info(request, message, extra_tags='wishlist')
        success = False

    return JsonResponse({'success': success, 'message': message})

def wishlist(request):
    try:
        wishlist_items = Wishlist.objects.filter(user=request.user)
    except MultipleObjectsReturned:
        wishlist_items = Wishlist.objects.filter(user=request.user).first()  # Get the first item
        Wishlist.objects.filter(user=request.user).exclude(id=wishlist_items.id).delete()  # Remove other duplicates

    # Filter messages that should only be displayed on the wishlist page
    messages_for_wishlist = [msg for msg in messages.get_messages(request) if 'wishlist' in msg.tags]

    context = {
        'wishlist_items': wishlist_items,
        'messages_for_wishlist': messages_for_wishlist
    }
    return render(request, 'user/wishlist.html', context)



def remove_from_wishlist(request, item_id):
    if request.method == 'POST':
        # Get the wishlist item for the current user
        wishlist_item = get_object_or_404(Wishlist, id=item_id, user=request.user)
        # Remove the item from the wishlist
        wishlist_item.delete()
        messages.success(request, "Item removed from wishlist.", extra_tags='wishlist')
    else:
        messages.error(request, "Invalid request method.", extra_tags='wishlist')
    return redirect('wishlist')

def toggle_wishlist(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'You need to be logged in to add items to your wishlist.'}, status=403)

    product = get_object_or_404(Product, id=product_id)
    wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()

    if wishlist_item:
        # Product is already in the wishlist, so remove it
        wishlist_item.delete()
        message = 'Product removed from your wishlist.'
    else:
        # Product is not in the wishlist, so add it
        Wishlist.objects.create(user=request.user, product=product)
        message = 'Product added to your wishlist.'

    return JsonResponse({'success': True, 'message': message})