from django.shortcuts import render, redirect
from .forms import UserRegisterForm, UserLoginForm
from.models import User
from django.contrib import messages
import re
from django.contrib.auth import authenticate, login as auth_login


def register(request):
    error_message = ''
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            if User.objects.filter(username=data['username']).exists():
                error_message = 'username already exists'
            elif User.objects.filter(email=data['email']).exists():
                error_message = 'email already exists'
            elif data['password_1'] != data['password_2']:
                error_message = 'passwords are not same'
            elif not re.search(r'\d', data['password_1']):
                error_message = 'password should include numbers'
            elif len(data['password_1']) < 8:
                error_message = 'length of password should be greater than 8'

            else:
                User.objects.create_user(username=data['username'], email=data['email'], password=data['password_1'])

                messages.success(request, 'your account created successfully')

                return redirect('home:home')
    else:
        form = UserRegisterForm

    context = {'form': form, 'error_message': error_message}

    return render(request, 'accounts/register.html', context)


def login(request):
    error_message = ''
    if request.method == 'POST':
        form = UserLoginForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            if not User.objects.filter(email=data['email']).exists():
                error_message = 'email not found'
            else:
                user = authenticate(request, username=data['email'], password=data['password'])

                user = User.objects.get(email=data['email'])
                if user.check_password(data['password']):
                    auth_login(request, user)

                    messages.success(request, 'you logged in successfully')

                    return redirect('home:home')

                else:
                    error_message = 'user not found'
    else:
        form = UserLoginForm()

    context = {'form': form, 'error_message': error_message}

    return render(request, 'accounts/login.html', context)
