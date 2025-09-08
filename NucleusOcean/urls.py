from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('golgavzaboon/', admin.site.urls),
    path('', include('home.urls', namespace='home')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
]
