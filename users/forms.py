from django.contrib.gis import forms
from django.forms import ModelForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from leaflet.forms.widgets import LeafletWidget
from phonenumber_field.formfields import PhoneNumberField
from allauth.account.models import EmailAddress
from users.models import Profile, Country, City

UserModel = get_user_model()


LEAFLET_WIDGET_ATTRS = {
    'map_height': '300px',
    'map_width': '100%',
    'map_srid': 4326,
}

class ProfileCreationForm(ModelForm):
    phone_number = PhoneNumberField(region="DZ")
    geo_location = forms.PointField(required=False, widget=LeafletWidget(attrs=LEAFLET_WIDGET_ATTRS))
    city = forms.ModelChoiceField(queryset=City.objects.all(), required=False)
    
    class Meta:
        model = Profile
        fields = ['profile_pic', 
                  'account_type', 
                  'phone_number', 
                  'bio', 
                  'city', 
                  'geo_location']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make sure to set required=False since we handle validation manually
        self.fields['geo_location'].required = False
        self.fields['city'].required = False
        
        # Set Algeria cities
        self.fields['city'].queryset = City.objects.filter(country__iso2='DZ')
    
    def clean(self):
        cleaned_data = super().clean()
        geo_data = cleaned_data.get('geo_location')
        city = cleaned_data.get('city')
        country = Country.objects.get(iso2='DZ')  # Algeria

        # Case 1: User selected geo_location but no city
        if geo_data and not city:
            # Validate country containment
            if not country.geom.contains(geo_data):
                self.add_error('geo_location', _('Location must be within Algeria'))
                return cleaned_data
            
            # Find the city containing the geo_location
            try:
                actual_city = City.objects.get(geom__contains=geo_data)
                cleaned_data['city'] = actual_city  # Assign the found city
            except City.DoesNotExist:
                self.add_error('geo_location', _('Location not within any known city'))
            except City.MultipleObjectsReturned:
                actual_city = City.objects.filter(geom__contains=geo_data).first()
                cleaned_data['city'] = actual_city
        
        # Case 2: User selected both geo_location and city
        elif geo_data and city:
            # Validate country containment
            if not country.geom.contains(geo_data):
                self.add_error('geo_location', _('Location must be within Algeria'))
                return cleaned_data
            
            # Validate city containment
            if not city.geom.contains(geo_data):
                try:
                    actual_city = City.objects.get(geom__contains=geo_data)
                    self.add_error('city', _('Location is in %(actual)s, not %(selected)s') % {
                        'actual': actual_city.name, 
                        'selected': city.name
                    })
                except City.DoesNotExist:
                    self.add_error('geo_location', _('Location not within any known city'))
        
        # Case 3: User selected city but no geo_location
        elif city and not geo_data:
            try:
                # Generate random location within city
                cleaned_data['geo_location'] = city.get_random_location_point()
            except Exception as e:
                self.add_error('city', _('Could not generate location for selected city'))
        
        # Case 4: User selected neither
        else:
            if not geo_data and not city:
                self.add_error(
                    'city',  # Non-field error
                    _('Please select either a location on the map or a city')
                )
        
        return cleaned_data

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = UserModel
        fields = ['username', 'first_name', 'last_name']


class ProfileUpdateForm(forms.ModelForm):
    phone_number = PhoneNumberField(region="DZ")

    class Meta:
        model = Profile
        fields = ['profile_pic', 'bio', 'account_type', 'phone_number']