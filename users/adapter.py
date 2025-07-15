from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.models import EmailAddress

class KhadraAccountAdapter(DefaultAccountAdapter):

    def get_signup_redirect_url(self, request):
        # Redirect users after sign up to profile creation
        return reverse('create-profile')

    def get_password_change_redirect_url(self, request):
        """
        The URL to redirect to after a successful password change/set.

        NOTE: Not called during the password reset flow.
        """
        return reverse('profile')

    def validate_unique_email(self, email):
        """
        Prevent duplicate emails even if ACCOUNT_UNIQUE_EMAIL fails
        """
        if EmailAddress.objects.filter(email=email).exists():
            raise ValidationError(_("This email is already in use by another account."))
        return email
    
    def clean_email(self, email):
        email = super().clean_email(email)
        return self.validate_unique_email(email)