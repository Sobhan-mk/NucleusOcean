from django.urls import path
from.views import home, about_developer


app_name = 'home'
urlpatterns = [
    path('', home, name='home'),
    path('about_developer/', about_developer, name='about_developer')
]