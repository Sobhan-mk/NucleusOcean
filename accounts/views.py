from django.shortcuts import render, redirect
from .forms import UserRegisterForm, UserLoginForm, UserUpdateForm, ProfileUpdateForm
from.models import User
from django.contrib import messages
import re
from django.contrib.auth import authenticate, login as auth_login, logout


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


def signout(request):
    logout(request)
    messages.success(request, 'you logged out successfully')

    return redirect('home:home')


def profile(request):
    if request.method == 'POST':
        user_update_form = UserUpdateForm(request.POST, instance=request.user)
        profile_update_form = ProfileUpdateForm(request.POST, instance=request.user.profile)

        if user_update_form.is_valid() and profile_update_form.is_valid():
            user_update_form.save()
            profile_update_form.save()

            messages.success(request, 'profile updated successfully')

            return redirect('home:home')

    else:
        user_update_form = UserUpdateForm(instance=request.user)
        profile_update_form = ProfileUpdateForm(instance=request.user.profile)

    context = {'user_update_form' : user_update_form,
               'profile_update_form' : profile_update_form}

    return render(request, 'accounts/profile.html', context)
