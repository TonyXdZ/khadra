from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        # Initiatives related notifications categories.
        ('initiative_created', _('Initiative Created')),
        ('initiative_approved', _('Initiative Approved')),
        ('initiative_review_failed', _('Initiative Review Failed')),
        ('initiative_started', _('Initiative Started')),
        ('initiative_cancelled', _('Initiative Cancelled')),
        ('initiative_completed', _('Initiative Completed')),
        # Announcement (for all users, no related object required)
        ('announcement', _('Announcement')),
        # Users related notifications categories
        ('upgrade_request_created', _('Upgrade Request Created')),
    ]

    notification_type = models.CharField(_('Notification type'), max_length=50, choices=NOTIFICATION_TYPES)
    message = models.TextField(_('Message')) 
    
    recipients = models.ManyToManyField(
        User,
        blank=True,
        related_name='notifications',
        verbose_name=_('Recipients'),
    )

    is_broadcast = models.BooleanField(
        _('Is broadcast'),
        default=False,
        help_text=_('If set to True the notification will be sent to all users.'),
    )

    # --- Generic relation fields ---
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    # Status
    is_read = models.BooleanField(_('Is read'), default=False)
    created_at = models.DateTimeField(_('Created at'), default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')

    def __str__(self):
        return f'Notification {self.pk} - {self.notification_type}'

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
    
    @staticmethod
    def get_for_user(user):
        """
        Get all notifications for a user.
        
        Returns direct notifications + broadcast notifications created after user joined.
        This prevents new users from seeing old announcement notifications.
        """
        return Notification.objects.filter(
            models.Q(recipients=user) | 
            (models.Q(is_broadcast=True) & 
             models.Q(created_at__gte=user.date_joined))
        ).distinct().order_by('-created_at')
