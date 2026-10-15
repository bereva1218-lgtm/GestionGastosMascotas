from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import include, path

from mascotas.forms import AccesoForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'cuentas/login/',
        LoginView.as_view(authentication_form=AccesoForm, redirect_authenticated_user=True),
        name='login',
    ),
    path('cuentas/', include('django.contrib.auth.urls')),
    path('', include('mascotas.urls')),
]
