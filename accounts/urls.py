from django.urls import path
from.views import register, login, signout, profile


app_name = 'accounts'
urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', signout, name='logout'),
    path('profile/', profile, name='profile'),
]