from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from users.models import Profile, City
from users.tests.test_utils import create_new_user
from users.messages import users_messages
from core.models import Initiative
from core.messages import core_messages


UserModel = get_user_model()

# Ovveriding prod spatial data with light weigth test layers to speed up tests
@override_settings(SPATIAL_LAYER_PATHS=settings.TEST_SPATIAL_LAYER_PATHS)
class InitiativesTestCase(TestCase):

    @classmethod
    def setUpTestData(self):
        call_command('load_spatial_layers', 'DZ')
        self.client_1 = Client()
        self.client_2 = Client()
        self.annaba_city = City.objects.get(name='Annaba')
        self.point_in_annaba = self.annaba_city.get_random_location_point()

    def test_user_with_account_type_volunteer_get_403_in_create_initiative_view(self):
        """
        Verify volunteer account users receive 403 Forbidden responses
        when attempting to GET or POST to initiative creation view,
        and no initiatives are created through unauthorized access.
        """
        volunteer_user = create_new_user(email='volunteer_user@gmail.com',
                                    username='volunteer_user',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='volunteer',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )

        self.client_1.login(username='volunteer_user', password='qsdflkjlkj')

        date_in_the_future = timezone.now() + timezone.timedelta(days=7)

        # Get create initiative view
        get_response = self.client_1.get(reverse('create-initiative'))

        # Post create initiative view
        post_response = self.client_1.post(reverse('create-initiative'),
                                        {
                                            'geo_location': str(self.point_in_annaba),
                                            'info': 'we need equipments transportation',
                                            'required_volunteers': '30',
                                            'scheduled_datetime': date_in_the_future.strftime('%d/%m/%Y %H:%M'),
                                            'duration_days': '3',
                                        })
        
        created_initiatives = Initiative.objects.all().count()
        self.assertEqual( get_response.status_code, 403)
        self.assertEqual( post_response.status_code, 403)
        self.assertEqual( created_initiatives, 0)

    def test_user_with_account_type_manager_can_create_initiative(self):
        """
        Verify manager account users can successfully access the initiative creation view
        and create new initiatives through valid POST requests.
        """
        manage_user = create_new_user(email='manage_user@gmail.com',
                                    username='manage_user',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='manager',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )

        self.client_1.login(username='manage_user', password='qsdflkjlkj')

        date_in_the_future = timezone.now() + timezone.timedelta(days=8)
        
        # Get create initiative view
        get_response = self.client_1.get(reverse('create-initiative'))

        # Post create initiative view
        post_response = self.client_1.post(reverse('create-initiative'),
                                        {
                                            'geo_location': str(self.point_in_annaba),
                                            'info': 'we need equipments transportation',
                                            'required_volunteers': '30',
                                            'scheduled_datetime': date_in_the_future.strftime('%d/%m/%Y %H:%M'),
                                            'duration_days': '3',
                                        })
        
        created_initiatives = Initiative.objects.all()
        new_initiative = created_initiatives.first()

        self.assertEqual( get_response.status_code, 200)
        self.assertEqual( new_initiative.city, self.annaba_city)
        self.assertEqual( new_initiative.created_by, manage_user)
        self.assertEqual( created_initiatives.count(), 1)

    def test_create_initiative_with_geo_location_outside_the_country(self):
        """
        Verify that initiatives cannot be created with geo_locations outside
        the country boundary, and that the appropriate error message is returned.
        """
        
        manage_user = create_new_user(email='manage_user@gmail.com',
                                    username='manage_user',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='manager',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )

        self.client_1.login(username='manage_user', password='qsdflkjlkj')

        date_in_the_future = timezone.now() + timezone.timedelta(days=7)
        # Geo location outside Algeria
        point_in_germany = 'SRID=4326;POINT (9.851 51.11)'
        
        post_response = self.client_1.post(reverse('create-initiative'),
                                        {
                                            'geo_location': point_in_germany,
                                            'info': 'we need equipments transportation',
                                            'required_volunteers': '30',
                                            'scheduled_datetime': date_in_the_future.strftime('%d/%m/%Y %H:%M'),
                                            'duration_days': '3',
                                        })
        created_initiatives = Initiative.objects.all().count()
        
        self.assertContains( post_response, users_messages['LOCATION_OUTSIDE_COUNTRY'])
        self.assertEqual( created_initiatives, 0)

    def test_user_cant_create_initiative_with_scheduled_datetime_in_the_past(self):
        """
        Verify that initiatives cannot be created with scheduled datetimes in the past,
        ensuring the appropriate error message is returned and no initiative is created.
        """
        manage_user = create_new_user(email='manage_user@gmail.com',
                                    username='manage_user',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='manager',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )

        self.client_1.login(username='manage_user', password='qsdflkjlkj')

        date_in_the_past = timezone.now() - timezone.timedelta(days=365)
        
        post_response = self.client_1.post(reverse('create-initiative'),
                                        {
                                            'geo_location': str(self.point_in_annaba),
                                            'info': 'we need equipments transportation',
                                            'required_volunteers': '30',
                                            'scheduled_datetime': date_in_the_past.strftime('%d/%m/%Y %H:%M'),
                                            'duration_days': '3',
                                        })
        
        created_initiatives = Initiative.objects.all().count()
        self.assertContains( post_response, core_messages['DATE_IN_THE_PAST'])
        self.assertEqual( created_initiatives, 0)

    def test_user_cant_create_initiative_with_scheduled_datetime_too_close(self):
        """
        Verify that initiatives cannot be scheduled within less than 7 days of the current date,
        ensuring the appropriate error message is returned and no initiative is created.
        """
        manage_user = create_new_user(email='manage_user@gmail.com',
                                    username='manage_user',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='manager',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )

        self.client_1.login(username='manage_user', password='qsdflkjlkj')

        date_in_less_than_week = timezone.now() + timezone.timedelta(days=5)
        
        post_response = self.client_1.post(reverse('create-initiative'),
                                        {
                                            'geo_location': str(self.point_in_annaba),
                                            'info': 'we need equipments transportation',
                                            'required_volunteers': '30',
                                            'scheduled_datetime': date_in_less_than_week.strftime('%d/%m/%Y %H:%M'),
                                            'duration_days': '3',
                                        })
        
        created_initiatives = Initiative.objects.all().count()
        self.assertContains( post_response, core_messages['DATE_TOO_CLOSE'])
        self.assertEqual( created_initiatives, 0)

    def test_initiative_review_can_be_created_by_manager(self):
        """
        Verify that initiatives reviews can be created by users
        with account type of manager.
        """
        manage_user = create_new_user(email='manage_user@gmail.com',
                                    username='manage_user',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='manager',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )
        # Reviewer has to be manager account type
        reviewer_user = create_new_user(email='reviewer_user@gmail.com',
                                    username='reviewer_user',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='manager',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )

        self.client_1.login(username='manage_user', password='qsdflkjlkj')
        self.client_2.login(username='reviewer_user', password='qsdflkjlkj')

        date_scheduled = timezone.now() + timezone.timedelta(days=8)
        
        # Create initiative by manager
        post_response = self.client_1.post(reverse('create-initiative'),
                                        {
                                            'geo_location': str(self.point_in_annaba),
                                            'info': 'we need equipments transportation',
                                            'required_volunteers': '30',
                                            'scheduled_datetime': date_scheduled.strftime('%d/%m/%Y %H:%M'),
                                            'duration_days': '1',
                                        })
        initiative = Initiative.objects.all().first()

        review_url = reverse('initiative-review', kwargs={'pk': str(initiative.pk)})
        
        # Get review view as a manager
        get_review_response = self.client_1.get(review_url)

        # Post a review as reviewer
        post_review_response = self.client_2.post(review_url, {'vote': 'approve'})
        
        reviews_created = initiative.reviews.all().count()
        
        self.assertEqual(reviews_created, 1)

    def test_initiative_review_restricted_for_volunteers(self):
        """
        Verify that initiatives reviews cannot be accessed by users
        with account type of volunteer.
        """
        manage_user = create_new_user(email='manage_user@gmail.com',
                                    username='manage_user',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='manager',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )

        volunteer_user = create_new_user(email='volunteer_user@gmail.com',
                                    username='volunteer_user',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='volunteer',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )

        self.client_1.login(username='manage_user', password='qsdflkjlkj')
        self.client_2.login(username='volunteer_user', password='qsdflkjlkj')
        date_scheduled = timezone.now() + timezone.timedelta(days=8)
        
        # Create initiative by manager
        post_response = self.client_1.post(reverse('create-initiative'),
                                        {
                                            'geo_location': str(self.point_in_annaba),
                                            'info': 'we need equipments transportation',
                                            'required_volunteers': '30',
                                            'scheduled_datetime': date_scheduled.strftime('%d/%m/%Y %H:%M'),
                                            'duration_days': '1',
                                        })
        initiative = Initiative.objects.all().first()
        
        review_url = reverse('initiative-review', kwargs={'pk': str(initiative.pk)})
        # Get initiative review by volunteer
        get_review_response = self.client_2.get(review_url)
        
        # Post a review as volunteer
        post_review_response = self.client_2.post(review_url, {'vote': 'reject'})
        
        reviews_created = initiative.reviews.all().count()
        
        self.assertEqual(get_review_response.status_code, 403)
        self.assertEqual(post_review_response.status_code, 403)
        self.assertEqual(reviews_created, 0)

    def test_initiative_review_restricted_for_the_creator(self):
        """
        Verify that managers can't review their own initiatives.
        """
        manage_user = create_new_user(email='manage_user@gmail.com',
                                    username='manage_user',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='manager',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )

        

        self.client_1.login(username='manage_user', password='qsdflkjlkj')
        
        date_scheduled = timezone.now() + timezone.timedelta(days=8)
        
        # Create initiative by manager
        post_response = self.client_1.post(reverse('create-initiative'),
                                        {
                                            'geo_location': str(self.point_in_annaba),
                                            'info': 'we need equipments transportation',
                                            'required_volunteers': '30',
                                            'scheduled_datetime': date_scheduled.strftime('%d/%m/%Y %H:%M'),
                                            'duration_days': '1',
                                        })
        initiative = Initiative.objects.all().first()
        
        review_url = reverse('initiative-review', kwargs={'pk': str(initiative.pk)})
        
        # Get initiative review as the initiative creator
        get_review_response = self.client_1.get(review_url)

        # Post a review as the initiative creator
        post_review_response = self.client_1.post(review_url, {'vote': 'approve'})
        
        reviews_created = initiative.reviews.all().count()
        
        self.assertEqual(get_review_response.status_code, 403)
        self.assertEqual(post_review_response.status_code, 403)
        self.assertEqual(reviews_created, 0)
        
