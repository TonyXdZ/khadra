from django.core.management.base import BaseCommand
from django.conf import settings
from users.models import Country, City, Profile
from django.contrib.gis.utils import LayerMapping

country_mapping = {
    'name': 'name',
    'iso2': 'iso2',
    'geom': 'MULTIPOLYGON',
}

city_mapping = {
    'name': 'name',
    'geom': 'MULTIPOLYGON',
}


class Command(BaseCommand):
    """
    Management command to Create/Update spatial data in database
    To create a new country in database:
    1- Add country shape files in /geodata/COUNTRY_ISO2/
    2- Add the cities shape files in  /geodata/COUNTRY_ISO2/Cities/
    3- Add path to the files in settings.SPATIAL_LAYER_PATHS
    Note: replace 'COUNTRY_ISO2' with your country ISO2 e.g: for Algeria DZ

    If the Country/Countries already exist in your database the command 
    will not modify them unless you use -u flag

    Using -u or --update flag will delete the Country/Countries 
    and cities from database and create new ones from files again.

    The command will keep the relation between Profile and Country/City 
    by reassigning the correct country and city
    based on geo_location field after update.

    Current models with relationship to Country and City models:
    
    - Profile
    """

    help = "Load spatial layers specified in settings.SPATIAL_LAYER_PATHS from 'geodata/prod_layers/' folder into the database"

    def add_arguments(self, parser):
        parser.add_argument('country_iso2', nargs='+', type=str, help='ISO2 code of Country/Countries to add to database')
        parser.add_argument('-u',
            '--update',
            action='store_true',
            help='Update Country/Countries and Cities if they already exist in database or create new ones if they do not exist')

    def save_country(self, country_iso2):
        country_and_cities = settings.SPATIAL_LAYER_PATHS.get(country_iso2)
        country_shape = country_and_cities.get('country')
        lm_country = LayerMapping(Country, country_shape, country_mapping, transform=False)
        lm_country.save(strict=True)
        self.stdout.write(self.style.SUCCESS("Saved %s country data successfully" % country_iso2))

    def save_cities(self, country_iso2):
        country_and_cities = settings.SPATIAL_LAYER_PATHS.get(country_iso2)
        cities_shape = country_and_cities.get('cities')
        lm_cities = LayerMapping(City, cities_shape, city_mapping, transform=False)
        lm_cities.save(strict=True)
        self.stdout.write(self.style.SUCCESS("Saved %s cities data successfully" % country_iso2))

    def handle(self, *args, **kwargs):
        country_ids = kwargs['country_iso2']
        update = kwargs['update']
        countries_in_settings = settings.SPATIAL_LAYER_PATHS

        for country in country_ids:
            if country in countries_in_settings:
                country_already_in_db = Country.objects.filter(iso2=country).exists()
                cities_already_in_db = City.objects.filter(country__iso2=country).exists()

                if country_already_in_db:
                    if not update:
                        self.stdout.write("'%s' already in your database, if you want to update it use -u or --update" % country)
                    else:
                        users_in_country = Profile.objects.filter(country__iso2=country)

                        country_to_delete = Country.objects.get(iso2=country)

                        self.save_country(country)
                        new_country = Country.objects.filter(iso2=country).last()

                        users_in_country.update(country=new_country)

                        country_to_delete.delete()

                        self.save_cities(country)

                        all_cities = City.objects.filter(country__iso2=country)
                        profiles_in_country = Profile.objects.filter(country__iso2=country)

                        for city in all_cities:
                            profiles_in_city = profiles_in_country.filter(geo_location__contained=city.geom)
                            profiles_in_city.update(city=city)

                if not country_already_in_db:
                    self.save_country(country)

                if not cities_already_in_db:
                    self.save_cities(country)

            else:
                self.stdout.write(self.style.ERROR("'%s' is not specified in settings.SPATIAL_LAYER_PATHS, make sure you add it and run the command again" % country))