from django.contrib.gis import forms
from django.forms import ModelForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from leaflet.forms.widgets import LeafletWidget
from phonenumber_field.formfields import PhoneNumberField
from allauth.account.models import EmailAddress
from users.models import Profile, Country, City
from users.messages import users_messages

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
                self.add_error('geo_location', users_messages['LOCATION_OUTSIDE_COUNTRY'])
                return cleaned_data
            
            # Find the city containing the geo_location
            try:
                actual_city = City.objects.get(geom__contains=geo_data)
                cleaned_data['city'] = actual_city  # Assign the found city
            except City.DoesNotExist:
                self.add_error('geo_location', users_messages['LOCATION_UNKNOWN_CITY'])
            except City.MultipleObjectsReturned:
                actual_city = City.objects.filter(geom__contains=geo_data).first()
                cleaned_data['city'] = actual_city
        
        # Case 2: User selected both geo_location and city
        elif geo_data and city:
            # Validate country containment
            if not country.geom.contains(geo_data):
                self.add_error('geo_location', users_messages['LOCATION_OUTSIDE_COUNTRY'])
                return cleaned_data
            
            # Validate city containment
            if not city.geom.contains(geo_data):
                try:
                    actual_city = City.objects.get(geom__contains=geo_data)
                    self.add_error('city', users_messages['LOCATION_OUTSIDE_CITY'] % {
                        'actual': actual_city.name, 
                        'selected': city.name
                    })
                except City.DoesNotExist:
                    self.add_error('geo_location', users_messages['LOCATION_UNKNOWN_CITY'])
        
        # Case 3: User selected city but no geo_location
        elif city and not geo_data:
            try:
                # Generate random location within city
                cleaned_data['geo_location'] = city.get_random_location_point()
            except Exception as e:
                self.add_error('city', users_messages['COULD_NOT_GENERATE_LOCATION_FOR_CITY'])
        
        # Case 4: User selected neither
        else:
            if not geo_data and not city:
                self.add_error(
                    'city',  # Non-field error
                    users_messages['SELECT_CITY_OR_LOCATION']
                )
        
        return cleaned_data

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = UserModel
        fields = ['username', 'first_name', 'last_name']


class ProfileUpdateForm(ModelForm):
    phone_number = PhoneNumberField(region="DZ")
    geo_location = forms.PointField(widget=LeafletWidget(attrs=LEAFLET_WIDGET_ATTRS), required=False)
    city = forms.ModelChoiceField(queryset=City.objects.all())
    
    class Meta:
        model = Profile
        fields = ['profile_pic', 
                  'phone_number', 
                  'bio', 
                  'city', 
                  'geo_location']

    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__( * args, ** kwargs)
        
        #  Set Algeria cities
        self.fields['city'].queryset = City.objects.filter(country__iso2='DZ')
    
    def clean(self):
        cleaned_data = super().clean()
        geo_data = cleaned_data.get('geo_location')
        city = cleaned_data.get('city')
        country = self.instance.country
        changed_data = self.changed_data
        
        if self.has_changed():
            #  User Changed the City without changing his Geo location
            #  Assign a random point location in the selected City automatically
            if changed_data.__contains__('city') and changed_data.__contains__('geo_location') is False:
                random_location = city.get_random_location_point()
                cleaned_data['geo_location'] = random_location# city.geom.point_on_surface
                self.instance.geo_location = random_location

            #  User Changed his Geo Location without changing his City
            #  Assign the City that contains the point location automatically
            elif changed_data.__contains__('geo_location') and changed_data.__contains__('city') is False:
            
                # Check if the chosen location is in the user's country
                if geo_data:
                    if country.geom.contains( geo_data ):
                        cleaned_data['city'] = City.objects.get(geom__contains=geo_data)
                    else:
                        self.add_error('geo_location', users_messages['LOCATION_OUTSIDE_COUNTRY'])
                else:
                    random_location = city.get_random_location_point()
                    cleaned_data['geo_location'] = random_location
                    self.instance.geo_location = random_location

            # User Changed Both his Geo Location and City
            elif changed_data.__contains__('geo_location') and changed_data.__contains__('city'):
                # Check if User select a location on the map
                if geo_data:
                    # Check if the chosen location is in the user's country
                    if country.geom.contains( geo_data ):
                        # Check if the location inside the chosen City
                        if city.geom.contains( geo_data ) :
                            cleaned_data['geo_location'] = geo_data
                            cleaned_data['city'] = city
                        # The chosen location is not in the selected City
                        else:
                            selected_city = City.objects.get(geom__contains=geo_data)
                            actual_city = City.objects.get(geom__contains=geo_data)
                            self.add_error('city', users_messages['LOCATION_OUTSIDE_CITY'] % {
                                            'actual': actual_city.name,
                                            'selected': city.name
                                        })
                    # The chosen location is not in the user's country
                    else:
                        self.add_error('geo_location', users_messages['LOCATION_OUTSIDE_COUNTRY'])
                # User cleared his Geo Location
                # Assign a random point location in the selected City automatically
                else:
                    random_location = city.get_random_location_point()
                    cleaned_data['geo_location'] = random_location
                    self.instance.geo_location = random_location

            # User Didn't change his Geo Locatio nor his City
            else:
                return cleaned_data