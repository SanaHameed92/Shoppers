from django.urls import path
from . import views

app_name = 'user_page'

urlpatterns = [
    path('user_list/',views.user_list,name='user_list'),
    path('user_delete/<int:user_id>/', views.user_delete, name='user_delete'),
    path('user_create/', views.user_create, name='user_create'),
    path('edit/<int:user_id>/', views.user_edit, name='user_edit'),
]