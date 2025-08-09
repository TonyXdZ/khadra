from django.utils import timezone
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from notifications.models import Notification


class NotificationsListView(LoginRequiredMixin, ListView):
    model = Notification
    paginate_by = 20
    context_object_name = 'notifications'
    template_name = 'notifications/notifications_list.html'

    def get_queryset(self, **kwargs):
        return Notification.get_for_user(user=self.request.user)
