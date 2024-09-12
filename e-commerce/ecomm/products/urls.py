
from django.urls import path
from . import views


    

app_name = 'product_page'

urlpatterns = [
    path('shop/',views.shop,name='shop'),
    path('shop-single/<int:product_id>/', views.shop_single, name='shop-single'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('remove-from-cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('product_filter_by_size/', views.product_filter_by_size, name='product_filter_by_size'),
    path('product_filter_by_color/', views.product_filter_by_color, name='product_filter_by_color'),
    path('checkout/',views.checkout,name='checkout'),
    path('update/', views.update_cart, name='update_cart'),
    path('order_summary/',views.order_summary,name='order_summary'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-success/<uuid:order_number>/', views.order_success, name='order_success'),
    path('proceed-to-pay/',views.razorpaycheck,name='razorpaycheck'),
    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons/add/', views.coupon_add, name='coupon_add'),
    path('coupons/edit/<int:pk>/', views.coupon_edit, name='coupon_edit'),
    path('coupons/delete/<int:pk>/', views.coupon_delete, name='coupon_delete'),
    path('variants/', views.list_product_variants, name='list_product_variants'),
    path('variants/add/', views.add_product_variant, name='add_product_variant'),
    path('variants/edit/<int:pk>/', views.edit_product_variant, name='edit_product_variant'),
    path('variants/delete/<int:pk>/', views.delete_product_variant, name='delete_product_variant'),
    path('confirm-order-razorpay/', views.confirm_order_razorpay, name='confirm_order_razorpay'),
    path('order-failed/', views.order_failed, name='order_failed'),
    path('order-success-after-failure/<str:order_number>/', views.order_success_after_failure, name='order_success_after_failure'),
    
    
    
    

]