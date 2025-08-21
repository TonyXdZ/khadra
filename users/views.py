from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView, DetailView
from users.models import Profile, Country, City, UpgradeRequest
from users.forms import (ProfileCreationForm, 
                        UserUpdateForm, 
                        ProfileUpdateForm, 
                        UpgradeRequestForm)
from users.messages import users_messages

UserModel = get_user_model()

class ProfileCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Profile
    form_class = ProfileCreationForm
    template_name = 'users/profile_create.html'
    success_url = reverse_lazy('home')

    def test_func(self):
        # User already have a profile
        if hasattr(self.request.user, 'profile') :
            self.permission_denied_message = users_messages['ALREAD_HAVE_PROFILE']
            return False
        else:
            self.user = self.request.user
            return True

    def form_valid(self, form):
        form.instance.user = self.request.user
        profile = form.save(commit=False)
        profile.country = Country.objects.get(iso2='DZ')
        profile.account_type = 'volunteer'
        profile.save()
        messages.success( self.request, users_messages['ACCOUNT_CREATED_SUCCESS'])
        return super().form_valid(form)


class MyProfileView(LoginRequiredMixin, TemplateView):
    
    template_name = 'users/profile.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data( ** kwargs)
        if not hasattr(self.request.user, 'profile'):
            messages.warning( self.request, users_messages['UNCOMPLETE_SIGN_UP_WARNING'])
            return redirect('create-profile')
        return render(request, self.template_name, context )


class ProfileUpdateView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile_update.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_form'] = UserUpdateForm(instance=self.request.user)
        context['profile_form'] = ProfileUpdateForm(instance=self.request.user.profile)
        return context

    def post(self, request, *args, **kwargs):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(self.request, users_messages['PROFILE_UPDATE_SUCCESS'])
            return redirect('profile')

        # If not valid, return context with bound forms (with errors)
        return self.render_to_response({
            'user_form': user_form,
            'profile_form': profile_form
        })

class PublicProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/public_profile.html'
    model = UserModel

    def get(self, request, *args, **kwargs):
        context = self.get_context_data( ** kwargs)
        user = get_object_or_404( UserModel, username=kwargs['username'] )

        if user == self.request.user:
            return redirect('profile')
        else:
            return render(request, self.template_name, context )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404( UserModel, username=kwargs['username'] )     
        context['user'] = user
        return context

class UpgradeRequestView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = UpgradeRequest
    template_name = 'users/upgrade_request.html'
    form_class = UpgradeRequestForm
    success_url = reverse_lazy('profile')

    def test_func(self):
        user = self.request.user

        # Check if user is already a manager
        if hasattr(user, "profile") and user.profile.account_type == "manager":
            self.permission_denied_message = users_messages["ALREADY_MANAGER"]
            return False

        # Check if user already has a pending request
        if user.upgrade_requests.filter(status="pending").exists():
            self.permission_denied_message = users_messages["ALREADY_HAVE_PENDING_REQUEST"]
            return False

        # Check if user already has an approved request
        if user.upgrade_requests.filter(status="approved").exists():
            self.permission_denied_message = users_messages["ALREADY_MANAGER"]
            return False

        # Otherwise, allow
        return True

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success( self.request, users_messages['UPGRADE_REQUEST_SUBMITTED'])
        return super().form_valid(form)