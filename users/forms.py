from django import forms
from django.forms import ModelForm
from django.contrib.auth import get_user_model
from phonenumber_field.formfields import PhoneNumberField
from allauth.account.models import EmailAddress
from users.models import Profile

UserModel = get_user_model()


class ProfileCreationForm(ModelForm):
    phone_number = PhoneNumberField(region="DZ")

    class Meta:
        model = Profile
        fields = ['profile_pic', 'account_type', 'phone_number', 'bio']


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = UserModel
        fields = ['username', 'first_name', 'last_name']


class ProfileUpdateForm(forms.ModelForm):
    phone_number = PhoneNumberField(region="DZ")

    class Meta:
        model = Profile
        fields = ['profile_pic', 'bio', 'account_type', 'phone_number']