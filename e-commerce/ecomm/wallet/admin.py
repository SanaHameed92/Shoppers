from django.contrib import admin
from django.contrib.auth.models import User
from . models import Referral, WalletTransaction,ReturnRequest

class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('order__order_number',)

admin.site.register(ReturnRequest, ReturnRequestAdmin)


admin.site.register(WalletTransaction)
# Register your models here.
class UserAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not Referral.objects.filter(user=obj).exists():
            Referral.objects.create(user=obj)


admin.site.register(User, UserAdmin)