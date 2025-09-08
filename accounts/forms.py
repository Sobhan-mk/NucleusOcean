from django import forms
from .models import User
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
