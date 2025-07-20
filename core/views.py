from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from core.forms import InitiativeCreationForm
from core.messages import core_messages
from users.models import Profile, City
from users.messages import users_messages


class HomeView(TemplateView):
    template_name = 'core/home.html'


class CreateInitiativeView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    template_name = 'core/create_initiative.html'
    success_url = reverse_lazy('profile') # NOTE: This will change to initiative details
    form_class = InitiativeCreationForm

    def test_func(self):
        # Check user type account of he is not manager raise 403
        if self.request.user.profile.account_type == 'manager' :
            self.user = self.request.user
            return True
        else:
            self.permission_denied_message = core_messages['MANAGERS_ONLY']
            return False

    def form_valid(self, form):
        geo_location = form.instance.geo_location
        # Assign City instance automatically from given geo_location
        form.instance.city = City.objects.get(geom__contains=geo_location)
        messages.success( self.request, core_messages['INITIATIVE_CREATED_SUCCESS'])
        return super().form_valid(form)