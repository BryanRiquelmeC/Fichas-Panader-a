from django.urls import path
from .views import login_view, logout_view, two_factor_view, menu_principal, register_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('two_factor_view/', two_factor_view, name='two_factor_view'),
    path('menu/', menu_principal, name='menu_principal'),
]
