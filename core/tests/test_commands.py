from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from users.tests.test_utils import create_new_user
from users.models import City, Country, Profile


# Ovveriding prod spatial data with light weigth test layers to speed up tests
@override_settings(SPATIAL_LAYER_PATHS=settings.TEST_SPATIAL_LAYER_PATHS)
class LoadSpatialDataTestCase(TestCase):

    # Test that a new country and its cities are properly added to the database
    def test_add_new_country_to_db(self):
        countries_before = Country.objects.all().count()
        cities_before = City.objects.all().count()

        call_command('load_spatial_layers', 'DZ')

        countries_after = Country.objects.all().count()
        cities_after = City.objects.all().count()

        self.assertEqual(countries_before, 0)
        self.assertEqual(cities_before, 0)
        self.assertEqual(countries_after, 1)
        self.assertEqual(cities_after, 58)  # Algeria has 58 City (Wilayas)

    # Test that an error message is shown when trying to load a country not defined in settings
    def test_add_new_country_not_specified_in_settings(self):
        out = StringIO()
        call_command('load_spatial_layers', 'XY', stdout=out)
        self.assertIn("'XY' is not specified in settings.SPATIAL_LAYER_PATHS", out.getvalue())

    # Test that loading an already existing country without the update flag warns the user
    def test_add_country_already_exists_in_db(self):
        call_command('load_spatial_layers', 'DZ')

        out = StringIO()
        call_command('load_spatial_layers', 'DZ', stdout=out)
        self.assertIn("'DZ' already in your database", out.getvalue())

    # Test that using the update flag still works when the country does not already exist in the database
    def test_update_country_does_not_exist_in_db(self):
        countries_before = Country.objects.all().count()
        cities_before = City.objects.all().count()

        call_command('load_spatial_layers', 'DZ', '--update')

        countries_after = Country.objects.all().count()
        cities_after = City.objects.all().count()

        self.assertEqual(countries_before, 0)
        self.assertEqual(cities_before, 0)
        self.assertEqual(countries_after, 1)
        self.assertEqual(cities_after, 58)  # Algeria has 58 City (Wilayas)

     # Test that updating a country does not break existing relationships in the Profile model
    def test_update_country_does_not_break_profile_relationships(self):
        call_command('load_spatial_layers', 'DZ')

        algeria = Country.objects.get(iso2='DZ')
        annaba = City.objects.get(name='Annaba')

        user_achref = create_new_user(
            email='achref@gmail.com',
            username='achref',
            password='qsdflkjlkj',
            phone_number='+213555447766', 
            bio='Some good bio for my little bro'
        )

        user_achref.profile.country = algeria
        user_achref.profile.city = annaba
        user_achref.profile.geo_location = annaba.geom.centroid
        user_achref.profile.save()

        self.assertEqual(user_achref.profile.country.name, 'Algeria')
        self.assertEqual(user_achref.profile.city.name, 'Annaba')

        call_command('load_spatial_layers', 'DZ', '-u')
        
        profile_achref = Profile.objects.get(user__username='achref')

        self.assertEqual(profile_achref.country.name, 'Algeria')
        self.assertEqual(profile_achref.city.name, 'Annaba')

        # Ensure the country and city have been replaced (different PKs)
        self.assertNotEqual(profile_achref.country.pk, algeria.pk)
        self.assertNotEqual(profile_achref.city.pk, annaba.pk)
