from django.shortcuts import render


def home(request):
    user = request.user.is_authenticated
    username = request.user.username if user else ''
    context = {'user_authenticated' : user, 'username' : username}
    return render(request, 'home/home.html', context)
