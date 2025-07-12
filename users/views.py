from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from users.models import Profile, Country, City
from users.forms import ProfileCreationForm, UserUpdateForm, ProfileUpdateForm


class ProfileCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Profile
    form_class = ProfileCreationForm
    template_name = 'users/profile_create.html'
    success_url = reverse_lazy('home')

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
        profile = form.save(commit=False)
        profile.country = Country.objects.get(iso2='DZ')
        profile.save()
        messages.success( self.request, _('Account created successfully'))
        return super().form_valid(form)


class MyProfileView(LoginRequiredMixin, TemplateView):
    
    template_name = 'users/profile.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data( ** kwargs)
        if not hasattr(self.request.user, 'profile'):
            messages.warning( self.request, _('You did not complete your sign up, please finish it to access all the features in the platform.'))
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
            messages.success(self.request, _('Profile updated successfully'))
            return redirect('profile')  # adjust to your URL name

        # If not valid, return context with bound forms (with errors)
        return self.render_to_response({
            'user_form': user_form,
            'profile_form': profile_form
        })