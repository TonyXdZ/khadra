from django.urls import reverse
from allauth.account.adapter import DefaultAccountAdapter


class KhadraAccountAdapter(DefaultAccountAdapter):

    def get_signup_redirect_url(self, request):
        #redirect users after sign up to profile creation
        return reverse('create-profile')

    def get_password_change_redirect_url(self, request):
        """
        The URL to redirect to after a successful password change/set.

        NOTE: Not called during the password reset flow.
        """
        return reverse('profile')