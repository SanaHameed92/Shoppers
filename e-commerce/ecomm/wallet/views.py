from django.http import JsonResponse
from django.shortcuts import render
from . models import CancellationRequest, Referral, WalletTransaction
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Order, ReturnRequest
from django.db.models import F
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST

# Create your views here.
def my_wallet(request):
    user = request.user
    transactions = WalletTransaction.objects.filter(user=user).order_by('-created_at')
    
    context = {
        'wallet_balance': user.wallet,  
        'transactions': transactions,
    }
    
    return render(request, 'user/my_wallet.html',context)



def request_return(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    if order.status == 'Delivered' and not hasattr(order, 'return_request'):
        # Create a return request
        ReturnRequest.objects.create(order=order, reason=request.POST.get('reason', 'No reason provided'))

        messages.success(request, 'Return request has been submitted.')
    else:
        messages.error(request, 'Return requests can only be made for delivered orders or a request already exists.')

    return redirect('order_detail', order_number=order_number)

def admin_confirm_return(request, return_request_id):
    return_request = get_object_or_404(ReturnRequest, id=return_request_id)
    order = return_request.order
    

    if return_request.status == 'Requested':
        # Start a transaction to ensure atomic operations
        with transaction.atomic():
            # Confirm the return request
            return_request.status = 'Confirmed'
            return_request.save()

            # Update order status
            order.status = 'Returned'
            order.payment_status = 'Refunded'
            order.save()

            # Get the user associated with the order
            user = order.user
            if user:
                # Calculate the refund amount after deducting the shipping charge
                refund_amount = order.grand_total - order.shipping_fee

                # Credit the wallet
                user.wallet += refund_amount
                user.save()

                # Record the wallet transaction
                WalletTransaction.objects.create(
                    user=user,
                    amount=refund_amount,
                    transaction_type='Credit',
                    description=f'Refund for order {order.order_number}'
                )

                # Update product quantities
                for item in order.items.all():
                    product = item.product
                    product.quantity += item.quantity
                    product.save()

                # Show success message
                messages.success(request, 'Return request confirmed, wallet credited, and product quantities updated.', extra_tags='order_detail')
            else:
                messages.error(request, 'User does not exist.', extra_tags='order_detail')

    else:
        messages.error(request, 'Return request cannot be confirmed.', extra_tags='order_detail')

    return redirect('order_detail_view', order_number=order.order_number) 

def admin_reject_return(request, return_request_id):
    return_request = get_object_or_404(ReturnRequest, id=return_request_id)

    if return_request.status == 'Requested':
        # Reject the return request
        return_request.status = 'Rejected'
        return_request.save()

        messages.success(request, 'Return request rejected.')
    else:
        messages.error(request, 'Return request cannot be rejected.')

    return redirect('admin_return_requests')

def admin_return_requests(request):
    search_query = request.GET.get('search', '')

    # Filter return requests based on search query
    return_requests = ReturnRequest.objects.all()
    if search_query:
        return_requests = return_requests.filter(
            Q(order__order_number__icontains=search_query) |
            Q(reason__icontains=search_query) |
            Q(status__icontains=search_query)
        )

    # Paginate the return requests
    paginator = Paginator(return_requests, 3)  # Show 10 return requests per page
    page_number = request.GET.get('page')
    return_requests_page = paginator.get_page(page_number)

    return render(request, 'admin_side/admin_return_requests.html', {
        'return_requests': return_requests_page,
        'search_query': search_query
    })


@login_required
def referral_page(request):
    referral = get_object_or_404(Referral, user=request.user)
    friends = referral.referred_friends.all()

    context = {
        'referral_code': referral.referral_code,
        'friends': friends,
    }
    return render(request, 'user/referral.html', context)



def request_cancel_order(request, order_number):
    if request.method == 'POST':
        reason = request.POST.get('reason')
        
        # Fetch the order for the current user
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        
        if order.status != 'Cancelled' or order.status != 'Delivered':
            # Create a cancellation request
            cancellation_request, created = CancellationRequest.objects.get_or_create(order=order)
            if created:
                cancellation_request.reason = reason
                cancellation_request.status = 'Pending'
                cancellation_request.save()
                messages.success(request, "Cancellation request submitted successfully. The admin will review it.")
            else:
                messages.info(request, "A cancellation request for this order already exists.")
        else:
            messages.info(request, "Order is already cancelled.")
    
    return redirect('order_detail', order_number=order_number)


@user_passes_test(lambda u: u.is_superuser)
def review_cancellation_requests(request):
    requests = CancellationRequest.objects.filter(status='Pending')
    return render(request, 'admin_side/review_cancellation_requests.html', {'requests': requests})

@user_passes_test(lambda u: u.is_superuser)
def process_cancellation_request(request, request_id, action):
    cancellation_request = get_object_or_404(CancellationRequest, id=request_id)
    order = cancellation_request.order

    if action == 'approve':
        # Update order and cancellation request statuses
        order.status = 'Cancelled'
        order.payment_status = 'Refunded'
        order.save()
        cancellation_request.status = 'Confirmed'
        
        # Restore product quantities
        for item in order.items.all():
            product = item.product
            product.quantity += item.quantity
            product.save()
        
        # Process the wallet refund
        user = order.user
        user.wallet += order.grand_total
        user.save()

        # Log the wallet transaction
        WalletTransaction.objects.create(
            user=user,
            transaction_type='Credit',
            amount=order.grand_total,
            description=f'Refund for cancelled order {order.order_number}'
        )
        
        messages.success(request, "Cancellation request approved and order cancelled.")
    elif action == 'reject':
        cancellation_request.status = 'Rejected'
        messages.success(request, "Cancellation request rejected.")
    
    # Save the updated cancellation request status
    cancellation_request.save()

    # Store details in the session to display after redirect
    request.session['cancellation_details'] = {
        'order_number': order.order_number,
        'requested_at': cancellation_request.requested_at.strftime("%Y-%m-%d %H:%M"),
        'status': cancellation_request.status,
        'admin_comment': cancellation_request.admin_comment,
        'reason': cancellation_request.reason,
    }

    # Redirect to the order detail page
    return redirect('order_detail_view', order_number=order.order_number)


@require_POST
def wallet_payment(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    user = request.user

    if order.grand_total > user.wallet:
        return JsonResponse({'status': 'error', 'message': 'Insufficient wallet balance.'})

    # Deduct from wallet
    user.wallet -= order.grand_total
    user.save()

    # Update order status
    order.payment_status = 'Completed'
    order.status = 'Ordered'
    order.save()

    # Log wallet transaction
    WalletTransaction.objects.create(
        user=user,
        transaction_type='Debit',
        amount=order.grand_total,
        description=f'Payment for Order {order_number}'
    )

    messages.success(request, 'Payment completed successfully with wallet.')
    return JsonResponse({'status': 'success', 'message': 'Payment successful.'})