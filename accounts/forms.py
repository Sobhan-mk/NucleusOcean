from django import forms
from .models import User, Profile
from django.contrib.auth.forms import ReadOnlyPasswordHashField


class UserCreateForm(forms.ModelForm):
    password_1 = forms.CharField(widget=forms.PasswordInput)
    password_2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_password_2(self):
        data = self.cleaned_data
        if data['password_1'] and data['password_2'] and data['password_1'] != data['password_2']:
            raise forms.ValidationError('passwords are not same')
        else:
            return data['password_2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set(self.password_2)
        if commit:
            user.save(using=self._db)

        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_password(self):
        return self.initial['password']


class UserRegisterForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'username'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'email'})
    )
    password_1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'password'})
    )
    password_2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'})
    )


class UserLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'password'}))


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']


class ProfileUpdateForm(forms.ModelForm):

    class Meta:
        model = Profile

        fields = ['first_name',
                  'last_name',
                  'birthdate',
                  'role',
                  'field_of_study',
                  'academy']

