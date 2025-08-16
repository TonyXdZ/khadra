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
from core.tests.test_utils import create_initiative


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
        self.algiers_city = City.objects.get(name='Alger') # 600 km from Annaba
        self.point_in_algiers = self.algiers_city.get_random_location_point()
        self.oran_city = City.objects.get(name='Oran') # 400 km from Algiers 1200 km from Annaba
        self.point_in_oran = self.oran_city.get_random_location_point()
        self.init_list_url = reverse('initiatives-list')
        

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
        
    # INITIATIVES LIST TESTS
    
    def test_manager_sees_all_status_in_initiatives_list(self):
        """
        Test that managers see initiatives with all allowed 
        statuses in itiatives list
        """
        manager = create_new_user(email='manager@gmail.com',
                                    username='manager',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='manager',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )
        
        # Create initiatives with different statuses
        upcoming = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)
        upcoming.status = 'upcoming'
        upcoming.save()
        ongoing = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)
        ongoing.status = 'ongoing'
        ongoing.save()
        
        under_review = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)
        under_review.status = 'under_review'
        under_review.save()
        
        completed = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)
        completed.status = 'completed'  # Should not appear
        completed.save()

        cancelled = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)
        cancelled.status = 'cancelled'  # Should not appear
        cancelled.save()
        
        review_failed = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)
        review_failed.status = 'review_failed'  # Should not appear
        review_failed.save()
        

        self.client_1.login(username='manager', password='qsdflkjlkj')
        
        response = self.client_1.get(self.init_list_url)
        
        self.assertEqual(response.status_code, 200)
        initiatives = response.context['initiatives']
        initiative_ids = [init.id for init in initiatives]
        
        self.assertIn(upcoming.id, initiative_ids)
        self.assertIn(ongoing.id, initiative_ids)
        self.assertIn(under_review.id, initiative_ids)
        self.assertNotIn(completed.id, initiative_ids)
        self.assertNotIn(cancelled.id, initiative_ids)
        self.assertNotIn(review_failed.id, initiative_ids)

    def test_manager_sees_distance_sorted_in_initiatives_list(self):
        """Test that managers see initiatives sorted by distance in itiatives list"""
        manager = create_new_user(email='manager@gmail.com',
                                    username='manager',
                                    password='qsdflkjlkj',
                                    phone_number='+213555447766', 
                                    bio='Some good bio',
                                    account_type='manager',
                                    city=self.annaba_city,
                                    geo_location=self.point_in_annaba,
                                    )
        
        # Create initiatives at different distances from Annaba
        close_init = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        # Same location as manager
                                        geo_location=self.point_in_annaba) 

        medium_init = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.algiers_city,
                                        # ~600KM far from manager
                                        geo_location=self.point_in_algiers)

        far_init = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.oran_city,
                                        # ~1000KM far from manager
                                        geo_location=self.point_in_oran)
        
        self.client_1.login(username='manager', password='qsdflkjlkj')
        response = self.client_1.get(self.init_list_url)
        
        self.assertEqual(response.status_code, 200)
        initiatives = list(response.context['initiatives'])
        
        # Should be ordered by distance (closest first)
        self.assertEqual(initiatives[0].id, close_init.id)
        self.assertEqual(initiatives[1].id, medium_init.id)
        self.assertEqual(initiatives[2].id, far_init.id)
        
        # Check that distance annotation exists
        self.assertTrue(hasattr(initiatives[0], 'distance'))
        self.assertTrue(initiatives[0].distance.km < initiatives[1].distance.km)

    
    def test_volunteer_sees_only_upcoming_ongoing_in_initiatives_list(self):
        """
        Test that volunteers only see upcoming and ongoing 
        initiatives in itiatives list
        """
        
        manager = create_new_user(email='manager@gmail.com',
                            username='manager',
                            password='qsdflkjlkj',
                            phone_number='+213555447766', 
                            bio='Some good bio',
                            account_type='manager',
                            city=self.annaba_city,
                            geo_location=self.point_in_annaba,
                            )

        volunteer = create_new_user(email='volunteer@gmail.com',
                            username='volunteer',
                            password='qsdflkjlkj',
                            phone_number='+213553447766', 
                            bio='Some good bio',
                            account_type='volunteer',
                            city=self.annaba_city,
                            geo_location=self.point_in_annaba,
                            )
        
        # Create initiatives with different statuses
        upcoming = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)
        upcoming.status = 'upcoming'
        upcoming.save()
        ongoing = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)
        ongoing.status = 'ongoing'
        ongoing.save()
        
        under_review = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)
        under_review.status = 'under_review'
        under_review.save()
        
        completed = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)
        completed.status = 'completed'  # Should not appear
        completed.save()

        cancelled = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)
        cancelled.status = 'cancelled'  # Should not appear
        cancelled.save()
        
        review_failed = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        geo_location=self.point_in_annaba)
        review_failed.status = 'review_failed'  # Should not appear
        review_failed.save()
        
        self.client_1.login(username="volunteer", password="qsdflkjlkj")
        response = self.client_1.get(self.init_list_url)
        
        self.assertEqual(response.status_code, 200)
        initiatives = response.context['initiatives']
        initiative_ids = [init.id for init in initiatives]
        
        self.assertIn(upcoming.id, initiative_ids)
        self.assertIn(ongoing.id, initiative_ids)
        self.assertNotIn(under_review.id, initiative_ids)
        self.assertNotIn(completed.id, initiative_ids)
        self.assertNotIn(review_failed.id, initiative_ids)
        self.assertNotIn(cancelled.id, initiative_ids)


    def test_volunteer_sees_distance_sorted_initiatives_initiatives_list(self):
        """Test that volunteers see initiatives sorted by distance in itiatives list"""

        manager = create_new_user(email='manager@gmail.com',
                            username='manager',
                            password='qsdflkjlkj',
                            phone_number='+213555447766', 
                            bio='Some good bio',
                            account_type='manager',
                            city=self.annaba_city,
                            geo_location=self.point_in_annaba,
                            )

        volunteer = create_new_user(email='volunteer@gmail.com',
                            username='volunteer',
                            password='qsdflkjlkj',
                            phone_number='+213553447766', 
                            bio='Some good bio',
                            account_type='volunteer',
                            city=self.annaba_city,
                            geo_location=self.point_in_annaba,
                            )
        
        # Create initiatives at different distances from Annaba
        # and change the status of each one to 'upcoming'
        # to make sure the volunteer can see them
        close_init = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.annaba_city,
                                        # Same location as volunteer
                                        geo_location=self.point_in_annaba) 
        close_init.status = 'upcoming'
        close_init.save()

        medium_init = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.algiers_city,
                                        # ~600KM far from volunteer
                                        geo_location=self.point_in_algiers)

        medium_init.status = 'upcoming'
        medium_init.save()

        far_init = create_initiative(created_by=manager,
                                        info="good initiative",
                                        city=self.oran_city,
                                        # ~1000KM far from volunteer
                                        geo_location=self.point_in_oran)
        far_init.status = 'upcoming'
        far_init.save()

        self.client_1.login(username="volunteer", password="qsdflkjlkj")
        response = self.client_1.get(self.init_list_url)
        
        initiatives = list(response.context['initiatives'])
        # Should be ordered by distance (closest first)
        self.assertEqual(initiatives[0].id, close_init.id)
        self.assertEqual(initiatives[1].id, medium_init.id)
        self.assertEqual(initiatives[2].id, far_init.id)
        self.assertTrue(initiatives[0].distance.km < initiatives[1].distance.km)

        
    def test_empty_queryset_in_initiatives_list(self):
        """Test behavior when no initiatives exist"""
        manager = create_new_user(email='manager@gmail.com',
                            username='manager',
                            password='qsdflkjlkj',
                            phone_number='+213555447766', 
                            bio='Some good bio',
                            account_type='manager',
                            city=self.annaba_city,
                            geo_location=self.point_in_annaba)
                            
        self.client_1.login(username='manager', password='qsdflkjlkj')
        response = self.client_1.get(self.init_list_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['initiatives']), 0)
        self.assertFalse(response.context['is_paginated'])