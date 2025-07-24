from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.utils import timezone
from django.utils.timezone import now
from django.utils.translation import gettext as _
from users.models import City

class Initiative(models.Model):

    STATUS_CHOICES = [
        ('under_review', _('Under Review')),
        ('upcoming', _('Upcoming')),
        ('ongoing', _('Ongoing')),
        ('completed', _('Completed')),
        ('review_failed',  _('Review Failed')),
        ('cancelled', _('Cancelled')),
    ]
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='under_review')

    info = models.TextField(_('Information'), blank=True, help_text=_('Additional information about the intiative like requests or notes.'))
    city = models.ForeignKey(City, verbose_name=_('City'), on_delete=models.SET_NULL, null=True, blank=True)
    geo_location = models.PointField(verbose_name=_('Geolocation'), srid=4326, null=True, blank=True)
    required_volunteers = models.PositiveIntegerField(_('Required volunteers'))
    
    volunteers = models.ManyToManyField(
        User,
        verbose_name=_('Volunteers'),
        related_name='initiatives_joined',
        blank=True
    )

    scheduled_datetime = models.DateTimeField(
        _('Scheduled date and time'), 
        help_text=_('When is the initiative is going to start')
    )

    duration_days = models.PositiveIntegerField(
        _('Duration (days)'),
        default=1,
        help_text=_('Number of days the initiative will last')
        )
    
    end_datetime = models.DateTimeField(
        _('End date and time'),
        help_text=_('When the initiative ends'),
        null=True,
        blank=True
    )
    
    date_created = models.DateTimeField(_('Date created'), default=timezone.now)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,verbose_name=_('Created by'), related_name='initiatives')

    def __str__(self):
        return f"initiative {self.pk}"

    class Meta:
        verbose_name = _('Initiative')
        verbose_name_plural = _('Initiatives')
    
    def get_end_datetime(self):
        """Calculate end_datetime if not set"""
        if not self.end_datetime and self.scheduled_datetime:
            return self.scheduled_datetime + timezone.timedelta(days=self.duration_days)
        return self.end_datetime


class InitiativeReview(models.Model):
    VOTE_CHOICES = [
        ('approve', _('Approve')),
        ('reject',  _('Reject')),
    ]
    initiative = models.ForeignKey(
        Initiative,
        on_delete=models.SET_NULL,
        related_name='reviews',
        verbose_name=_('Initiative'),
        null=True,
    )
    manager = models.ForeignKey(User,
        on_delete=models.SET_NULL,
        related_name='initiative_reviews',
        verbose_name=_('Manager'),
        null=True,
    )
    vote = models.CharField(_('Vote'), max_length=7, choices=VOTE_CHOICES)
    date_reviewed = models.DateTimeField(_('Date Reviewed'), default=timezone.now)

    class Meta:
        unique_together = ('initiative', 'manager')
        verbose_name = _('Initiative Review')
        verbose_name_plural = _('Initiatives Reviews')

    def __str__(self):
        return f"initiative {self.pk} review"
