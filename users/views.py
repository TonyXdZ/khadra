from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from users.models import Profile
from users.forms import ProfileCreationForm

class ProfileCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Profile
    form_class = ProfileCreationForm
    template_name = 'users/profile_create.html'

    def test_func(self):
        # User already have a profile
        if hasattr(self.request.user, 'profile') :
            self.permission_denied_message = _('You already have beautiful profile')
            return False
        else:
            self.user = self.request.user
            return True

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.save()
        messages.success( self.request, _('Account created succefully'))
        return redirect('/')


class MyProfileView(LoginRequiredMixin, TemplateView):
    model = Profile
    template_name = 'users/profile.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data( ** kwargs)
        if not hasattr(self.request.user, 'profile'):
            messages.warning( self.request, _('You did not complete your sign up, please finish it to access all the features in the platform.'))
            return redirect('create-profile')
        return render(request, self.template_name, context )