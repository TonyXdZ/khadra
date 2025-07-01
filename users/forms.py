from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from phonenumber_field.formfields import PhoneNumberField
from users.models import Profile

class ProfileCreationForm(ModelForm):
    phone_number = PhoneNumberField(region="DZ")

    class Meta:
        model = Profile
        fields = ["account_type", "phone_number", "bio"]