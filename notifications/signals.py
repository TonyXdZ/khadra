from django.contrib.auth import get_user_model
from django.dispatch import Signal
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Initiative
from notifications.models import Notification

User = get_user_model()

initiative_approved_signal = Signal()

@receiver(post_save, sender=Initiative)
def notify_managers_initiative_created(sender, instance, created, **kwargs):
    """
    This signal is automatically emitted when a new initiative created.

    Notify all users with account type manager to review
    new initiative (except the initiative creator).
    """
    if created:
        managers = User.objects.filter(profile__account_type='manager').exclude(id=instance.created_by.id)

        notification = Notification.objects.create(
            notification_type='initiative_created',
            related_initiative=instance)
        
        notification.recipients.add(*managers)


@receiver(initiative_approved_signal)
def handle_initiative_approval(sender, instance, **kwargs):
    """
    This signal is emitted from core.tasks.evaluate_initiative_reviews_task
    when the initiative is approved successfully.

    Notify the creator of the initiative.
    """
    notification = Notification.objects.create(
        notification_type='initiative_approved',
        related_initiative=instance
    )
    notification.recipients.add(instance.created_by)