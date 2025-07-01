from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from django.views.generic.edit import CreateView
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
