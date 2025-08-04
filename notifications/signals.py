from django.contrib.auth import get_user_model
from django.dispatch import Signal
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Initiative
from notifications.models import Notification

User = get_user_model()

initiative_approved_signal = Signal()
initiative_review_failed_signal = Signal()
initiative_started_signal = Signal()
initiative_completed_signal = Signal()


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


@receiver(initiative_review_failed_signal)
def handle_initiative_review_failed(sender, instance, reason, **kwargs):
    """
    This signal is emitted from core.tasks.evaluate_initiative_reviews_task
    when the initiative evaluation failed due to lack of reviews or majority
    of 'reject' reviews by managers.

    Notify the creator of the initiative.
    
    Args:
        reason (str): reason for evaluation failure can be 'lack_of_reviews'
        or 'rejected_by_managers'.
    """
    notification = Notification.objects.create(
        notification_type='initiative_review_failed',
        related_initiative=instance,
        message=reason,
    )
    notification.recipients.add(instance.created_by)


@receiver(initiative_started_signal)
def handle_initiative_started_signal(sender, instance, **kwargs):
    """
    This signal is emitted from core.tasks.transition_initiative_to_ongoing_task
    when the initiative starts.

    Notify volunteers and initiative creator.
    """
    notification = Notification.objects.create(
        notification_type='initiative_started',
        related_initiative=instance
    )
    volunteers = instance.volunteers.all()
    notification.recipients.add(instance.created_by)

    if volunteers.exists():
        notification.recipients.add(*volunteers)


@receiver(initiative_completed_signal)
def handle_initiative_completed_signal(sender, instance, **kwargs):
    """
    This signal is emitted from core.tasks.transition_initiative_to_completed_task
    when the initiative is completed.

    Notify volunteers and initiative creator.
    """
    notification = Notification.objects.create(
        notification_type='initiative_completed',
        related_initiative=instance
    )
    volunteers = instance.volunteers.all()
    notification.recipients.add(instance.created_by)

    if volunteers.exists():
        notification.recipients.add(*volunteers)