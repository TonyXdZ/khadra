from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Initiative
from notifications.models import Notification

User = get_user_model()

@receiver(post_save, sender=Initiative)
def notify_managers_initiative_created(sender, instance, created, **kwargs):
    """
    Notify all users with account type manager to review
    new initiative (except the initiative creator).
    """
    if created:
        managers = User.objects.filter(profile__account_type='manager').exclude(id=instance.created_by.id)

        notification = Notification.objects.create(
            notification_type='initiative_created',
            related_initiative=instance)
        
        notification.recipients.add(*managers)

