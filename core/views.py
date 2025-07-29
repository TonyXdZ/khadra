from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic.edit import CreateView
from django.views.generic.detail import DetailView
from django.views.generic import TemplateView
from core.forms import InitiativeCreationForm, InitiativeReviewForm
from core.models import Initiative
from core.messages import core_messages
from core.tasks import evaluate_initiative_reviews_task
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
        form.instance.created_by = self.request.user
        messages.success( self.request, core_messages['INITIATIVE_CREATED_SUCCESS'])
        # Schedule initiaitve reviews evaluation task
        eta_time = timezone.now() + timedelta(days=settings.INITIATIVE_REVIEW_DURATION)
        evaluate_initiative_reviews_task.apply_async(args=[form.instance.id], eta=eta_time)  
        return super().form_valid(form)

class InitiativeDetails(LoginRequiredMixin, DetailView):
    template_name = 'core/initiative_detail.html'
    model = Initiative

    def get_context_data(self, *args, **kwargs):
        context = super(InitiativeDetails, self).get_context_data(*args, **kwargs)
        initiative = context["initiative"]
        joined_volunteers = initiative.volunteers.all()
        joined_volunteers_count = joined_volunteers.count()
        volunteers_percentage = (joined_volunteers_count / initiative.required_volunteers) * 100 if initiative.required_volunteers > 0 else 0
        context["joined_volunteers"] = joined_volunteers
        context["joined_volunteers_count"] = joined_volunteers_count
        context["volunteers_percentage"] = volunteers_percentage
        
        # Check if user has reviewed
        user_has_reviewed = False
        if self.request.user.is_authenticated and hasattr(self.request.user, 'profile') and self.request.user.profile.account_type == 'manager':
            # Check if a review exists for this initiative by this user
            user_has_reviewed = initiative.reviews.filter(manager=self.request.user).exists()

        context['user_has_reviewed'] = user_has_reviewed
        return context

class InitiativeReviewView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    template_name = 'core/initiative_review.html'
    model = Initiative

    def test_func(self):
        """
        Determines if the current user can access the review view for the initiative.
        Managers can review initiatives that are 'under_review' and haven't reviewed yet.
        """
        initiative = self.get_object()

        # 1. Check if the initiative is in the correct status
        if initiative.status != 'under_review':
            self.permission_denied_message = core_messages['INITIATIVE_NOT_UNDER_REVIEW']
            return False

        # 2. Check if the user is a manager
        if self.request.user.profile.account_type != 'manager':
            self.permission_denied_message = core_messages['MANAGERS_ONLY']
            return False

        # 3. Check if the user is the creator of the initiative
        if self.request.user == initiative.created_by:
            self.permission_denied_message = core_messages['USER_IS_INITIATIVE_CREATOR']
            return False

        # 4. Check if the manager has already reviewed this initiative
        existing_review = initiative.reviews.filter(manager=self.request.user).first()
        if existing_review:
            self.permission_denied_message = core_messages['MANAGER_REVIEWED_ALREADY']
            return False

        # If all checks pass, grant access
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the review form to the context for GET requests
        context['review_form'] = InitiativeReviewForm() # Pass initial data if needed
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object() # Get the initiative instance
        form = InitiativeReviewForm(self.request.POST)

        # Optional: Add checks here if the user is eligible to review this initiative
        # e.g., if request.user.is_manager and request.user not in self.object.volunteers.all()...

        if form.is_valid():
            review = form.save(commit=False)
            review.initiative = self.object # Associate with the current initiative
            review.manager = self.request.user   # Associate with the current logged-in user (manager)
            review.save()
            messages.success(request, _("Your review has been submitted successfully. Thanks!"))
            # Redirect to the detail page
            return redirect('initiative-detail', pk=self.object.pk)
        else:
            # If the form is invalid, re-render the detail view with the form errors
            context = self.get_context_data()
            context['review_form'] = form # Pass the invalid form back to the template
            return self.render_to_response(context)
