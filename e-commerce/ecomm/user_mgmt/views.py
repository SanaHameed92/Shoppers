from django.shortcuts import get_object_or_404, redirect, render
from accounts.models import Account
from .forms import UserCreationForm
from .forms import UserEditForm
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator


# Create your views here.
def user_list(request):
    search_query = request.GET.get('search', '')
    if search_query:
        users = Account.objects.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )
    else:
        users = Account.objects.all()

    # Pagination
    paginator = Paginator(users, 6)  # Show 6 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'admin_side/user_list.html', context)


def user_delete(request, user_id):
    user = get_object_or_404(Account, id=user_id)
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        return redirect('user_page:user_list')
    return render(request, 'admin_side/confirm_delete_user.html', {'user': user})

    
def user_create(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user_page:user_list')
    else:
        form = UserCreationForm()
    
    return render(request, 'admin_side/user_create.html', {'form': form})

def user_edit(request, user_id):
    user = get_object_or_404(Account, id=user_id)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User details updated successfully.')
            return redirect('user_page:user_list')
    else:
        form = UserEditForm(instance=user)
    
    return render(request, 'admin_side/user_edit.html', {'form': form, 'user': user})
