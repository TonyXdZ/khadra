from django.urls import reverse
from allauth.account.adapter import DefaultAccountAdapter


class KhadraAccountAdapter(DefaultAccountAdapter):

    def get_signup_redirect_url(self, request):
        #redirect users after sign up to profile creation
        return reverse('create-profile')