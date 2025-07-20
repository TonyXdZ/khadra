from django.contrib.gis import forms
from django.forms import ModelForm
from django.utils.translation import gettext as _
from leaflet.forms.widgets import LeafletWidget
from users.models import Country, City
from core.models import Initiative
from users.messages import users_messages
from django.forms import DateTimeInput


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