from django.contrib.gis import forms
from django.forms import ModelForm, DateTimeInput
from django.utils import timezone
from django.utils.translation import gettext as _
from leaflet.forms.widgets import LeafletWidget
from users.models import Country
from core.models import Initiative, InitiativeReview
from users.messages import users_messages
from core.messages import core_messages



LEAFLET_WIDGET_ATTRS = {
    'map_height': '300px',
    'map_width': '100%',
    'map_srid': 4326,
}


class InitiativeCreationForm(ModelForm):
    geo_location = forms.PointField(widget=LeafletWidget(attrs=LEAFLET_WIDGET_ATTRS))
    scheduled_datetime = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M', '%d/%m/%Y %H:%M'],
        widget=forms.DateTimeInput(
            attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            },
        )
    )
    
    class Meta:
        model = Initiative
        fields = ['geo_location', 
                  'info', 
                  'required_volunteers', 
                  'scheduled_datetime', 
                  'duration_days']

    def clean_geo_location(self):
        geo_location = self.cleaned_data['geo_location']
        country = Country.objects.get(iso2='DZ')  # Algeria

        # User selected geo_location outside country
        if not country.geom.contains(geo_location):
            raise forms.ValidationError(users_messages['LOCATION_OUTSIDE_COUNTRY'])
        return geo_location
    
    def clean_scheduled_datetime(self):
        date_time = self.cleaned_data['scheduled_datetime']
        
        # User selected a date in the past
        if date_time < timezone.now():
            raise forms.ValidationError(core_messages['DATE_IN_THE_PAST'])
        else:
            if date_time - timezone.now() < timezone.timedelta(days=7):
                raise forms.ValidationError(core_messages['DATE_TOO_CLOSE'])
        return date_time


class InitiativeReviewForm(ModelForm):
    
    class Meta:
        model = InitiativeReview
        fields = ['vote']