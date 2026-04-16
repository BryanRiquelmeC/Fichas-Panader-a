from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from accounts.views import login_view, logout_view, two_factor_view, menu_principal, register_view
from fichas.views import (
    lista_fichas,
    detalle_ficha,
    autocomplete_fichas,
    calcular_ajax,
    api_fichas_list,
    api_ficha_detalle,
)

urlpatterns = [
    #  raíz "/" mande al login
    path('', RedirectView.as_view(pattern_name='login', permanent=False)),

    path('admin/', admin.site.urls),

    # AUTH
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('two_factor_view/', two_factor_view, name='two_factor_view'),
    path('menu/', menu_principal, name='menu_principal'),

    # FICHAS 
    path('fichas/', lista_fichas, name="lista_fichas"),
    path('ficha/<int:id>/', detalle_ficha, name="detalle_ficha"),
    path('autocomplete/', autocomplete_fichas, name='autocomplete_fichas'),
    path('ficha/<int:id>/calcular/', calcular_ajax, name='calcular_ajax'),

    # API
    path('api/fichas/', api_fichas_list, name='api_fichas_list'),
    path('api/fichas/<int:id>/', api_ficha_detalle, name='api_ficha_detalle'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)