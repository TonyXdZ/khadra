from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from phonenumber_field.modelfields import PhoneNumberField
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill


class Profile(models.Model):
    """
    Holds addintional information about every user
    """

    ACCOUNT_TYPE_CHOICES = (
        ('volunteer', _('Volunteer')),
        ('manager', _('Manager')),
        )
    
    user = models.OneToOneField(User, verbose_name=_('User'), on_delete=models.CASCADE)
    account_type = models.CharField(_('Account type'), max_length=100, choices=ACCOUNT_TYPE_CHOICES, blank=True, null=True)
    
    #Original size profile pic
    profile_pic = models.ImageField(_("Profile picture"), default=None, upload_to='profile_pics', blank=True, null=True)

    #Thumbnail of profile pic to be displayed in the profile page
    profile_pic_256 = ImageSpecField(source='profile_pic',
        processors=[ResizeToFill(256, 256)],
        format='JPEG',
        options={'quality': 100})

    #Thumbnail of profile pic to be displayed in feed and maps page along side the username
    profile_pic_64 = ImageSpecField(source='profile_pic',
        processors=[ResizeToFill(64, 64)],
        format='JPEG',
        options={'quality': 100})

    phone_number = PhoneNumberField(_('Phone number'), help_text=_('Personal phone number'))
    bio = models.TextField(
        _('Biography'),
        max_length=500, 
        blank=True, 
        null=True,
        help_text=_('Tell us about yourself (500 characters max)')
    )

    def __str__(self):
        return f'{self.user.username} profile'

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')